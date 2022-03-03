import json
import os

import geojson
import pandas as pd
from django.conf import settings
import folium
from folium.plugins import HeatMapWithTime
from loguru import logger
import numpy as np

import business.save_geojson
from business.save_geojson import make_heat, make_map_only, get_colormap_gradient
from common.utils import return_location, get_background_url


def matching_result_map(dataset_file, task_id, background_id):
    """
    交通预测，生成结果地图文件，文件名：数据集名称_task_id_result.html

    :param dataset_file: 数据集文件对象 对应表 tb_file
    :param task_id: 任务id
    :param background_id: 地图底图id
    :return:
    """
    dataset_dir = dataset_file.extract_path
    # 准备result.json
    result_json_path = None
    result_dir = settings.EVALUATE_PATH_PREFIX + str(task_id) + settings.EVALUATE_PATH_SUFFIX
    file_list = os.listdir(result_dir)
    for file in file_list:
        if file.endswith(".npz"):
            result_json_path = result_dir + file
    print(result_json_path)
    # 准备dataset dyna json
    dataset_dir = dataset_dir + "_geo_json"
    dataset_json_path = None
    dataset_grid_json_path = None
    file_list = os.listdir(dataset_dir)
    for file in file_list:
        if file.count('dyna') > 0 and file.count("truth_dyna") == 0:
            dataset_json_path = dataset_dir + os.sep + file
        elif file.count('grid') > 0:
            dataset_grid_json_path = dataset_dir + os.sep + file
    # print(dataset_json_path)
    # 生成地图
    if result_json_path and dataset_json_path:
        logger.info("The result json path is: " + result_json_path)
        logger.info("The dataset json path is: " + dataset_json_path)
        map_save_path = settings.ADMIN_FRONT_HTML_PATH + dataset_file.file_name + "_" + str(task_id) + "_result.html"
        try:
            render_to_map(dataset_json_path, result_json_path, background_id, map_save_path)
        except Exception as ex:
            logger.error('render_to_map异常：{}', ex)
    elif result_json_path and dataset_grid_json_path:
        logger.info("The result json path is: " + result_json_path)
        logger.info("The dataset json path is: " + dataset_grid_json_path)
        map_save_path = settings.ADMIN_FRONT_HTML_PATH + dataset_file.file_name + "_" + str(task_id) + "_result.html"
        try:
            render_grid_to_map(dataset_grid_json_path, result_json_path, background_id, map_save_path,dataset_dir)
        except Exception as ex:
            logger.error('render_grid_to_map异常：{}', ex)
    else:
        logger.info("result json not found")


def render_to_map(dataset_json_path, result_json_path, background_id, map_save_path):
    dataset_json_content = json.load(open(dataset_json_path, 'r'))
    file_data = np.load(result_json_path)
    prediction = file_data['prediction']
    truth = file_data['truth']
    if len(prediction[0][0][0]) == 2:
        prediction = prediction.sum(axis=3)
        truth = truth.sum(axis=3)
    dif = prediction-truth
    list_hm_pre, geo_pre = make_series_list(prediction, dataset_json_path)
    list_hm_tru, geo_tru = make_series_list(truth, dataset_json_path)
    list_hm_dif, geo_dif = make_series_list(dif, dataset_json_path)
    m = folium.Map(
        location=return_location(dataset_json_content),
        tiles=get_background_url(background_id),
        zoom_start=12, attr='default'
    )
    colormap, gradient_map = get_colormap_gradient(geo_pre['features'], 'traffic_speed')
    HeatMapWithTime(list_hm_tru, name='truth',min_opacity=1,
                    radius=25, gradient=gradient_map).add_to(m)
    HeatMapWithTime(list_hm_pre,name='prediction', min_opacity=1,
                    radius=25, gradient=gradient_map).add_to(m)
    HeatMapWithTime(list_hm_dif, name='difference', min_opacity=1,
                    radius=25, gradient=gradient_map).add_to(m)
    colormap.add_to(m)
    for feature in geo_pre['features']:
        make_map_only(feature, [], m, 'traffic_speed')
    # folium.GeoJson(data=geo_pre, name='prediction').add_to(m)
    folium.LayerControl(sortLayers=True).add_to(m)
    logger.info("The task result file was generated successfully, html path: " + map_save_path)
    m.save(map_save_path)


def make_series_list(result, dataset_json_path):
    # result [B,T,N,F] T个时间，N个位置，F个特征
    if result.ndim == 4:
        result = result.reshape(len(result), len(result[0]), len(result[0][0]))
    # result = result.reshape(len(result), len(result[0]), len(result[0][0]))
    # 一共count_time个时间步和每个时间步geo_count个位置
    count_time = len(result[0])
    geo_count = len(result[0][0])
    result = np.array(result)
    result_mean1 = result.mean(axis=0)
    geo_mean = result_mean1.mean(axis=0)
    heat_list = []
    geo_list = []
    for i in result_mean1:
        time_list = []
        for j in i:
            item = [j]
            time_list.append(item)
        heat_list.append(time_list)
    for e in geo_mean:
        geo_list.append([e])
    view_json = json.load(open(dataset_json_path, 'r'))
    # 将坐标和特征值组合
    for i in range(len(heat_list)):
        k = 0
        for _ in view_json['features']:
            location = business.save_geojson.return_location(_)
            # print(location)
            heat_list[i][k].insert(0, location[1])
            heat_list[i][k].insert(1, location[0])
            k += 1
    index = 0
    for feature in view_json['features']:
        location = business.save_geojson.return_location(feature)
        # print(location)
        geo_list[index].insert(0, location[1])
        geo_list[index].insert(1, location[0])
        index += 1
    heat_time_list = []
    # 在通过heat_list构造geojson、
    geo = generate_geojson(geo_list)
    # 二维heat_list降为一维heat_time_list
    for loc in range(len(heat_list[0])):
        for time in range(len(heat_list)):
            heat_time_list.append(heat_list[time][loc])
    # 归一化
    heat_time_list = make_heat(heat_time_list)
    list_hm = []
    for i in range(count_time):
        list_item = []
        for k in range(geo_count):
            list_k = heat_time_list[k * count_time:(k + 1) * count_time]
            list_item.append(list_k[i])
        list_hm.append(list_item)
    return list_hm, geo


def generate_geojson(geo_list):
    # geo_list 207 * 3[lat, lng, speed]
    # 构造geojson数据，经纬度要反转一下，特征值放properties里面
    features = []
    for e in geo_list:
        # 是否特征值只有traffic_speed
        properties = {'traffic_speed': float(e[2])}
        point = geojson.Point((float(e[1]), float(e[0])))
        feature_json = geojson.Feature(geometry=point, properties=properties)
        features.append(feature_json)
    return geojson.FeatureCollection(features)


def render_grid_to_map(dataset_grid_json_path, result_json_path, background_id, map_save_path,dataset_dir):
    dataset_json_content = json.load(open(dataset_grid_json_path, 'r'))
    file_data = np.load(result_json_path)
    prediction = file_data['prediction']
    truth = file_data['truth']
    dif = prediction-truth
    m = folium.Map(
        location=return_location(dataset_json_content),
        tiles=get_background_url(background_id),
        zoom_start=12, attr='default'
    )
    print(123)
    make_cor(prediction, m, dataset_json_content,dataset_dir,name='pre_Choropleth')
    print(1234)
    make_cor(truth, m, dataset_json_content,dataset_dir,name='truth_Choropleth')
    make_cor(dif, m, dataset_json_content,dataset_dir,name='differ_Choropleth')
    folium.LayerControl().add_to(m)
    logger.info("The task result file was generated successfully, html path: " + map_save_path)
    m.save(map_save_path)


def make_cor(data, m, dataset_json_content,dataset_dir,name):
    data = data.reshape(len(data), -1, 2)
    data_mean = data.mean(axis=0)
    data_mean = data_mean.mean(axis=1)
    data_list = []
    for item in data_mean:
        data_list.append([item])
    print(data_list)
    # data_list = np.array(data_list)
    list_geoid = []
    for _ in dataset_json_content['features']:
        list_geoid.append(int(_['id']))
    # list_geoid = np.array(list_geoid)
    print(list_geoid)
    i = 0
    for item in list_geoid:
        data_list[i].insert(0,item)
        i+=1
    # np.insert(data_list, 0, list_geoid,axis=1)
    print(data_list)
    data_list = np.array(data_list)
    csv_url = dataset_dir + "/form_cor.csv"
    np.savetxt(csv_url,data_list, delimiter=',')
    print(12345)
    df = pd.read_csv(csv_url, header=None, names=['geo_id', 'sum_inflow_outflow'])
    df.to_csv(csv_url, index=False)
    print(123456)
    try:
        business.save_geojson.add_Choropleth(csv_url, m, state_geo=dataset_json_content, tag1='inflow', tag2='outflow',name=name)
        print(12)
    except Exception:
        pass
