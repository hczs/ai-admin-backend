import json
import os
from django.conf import settings
import folium
from folium.plugins import HeatMapWithTime
from loguru import logger
import numpy as np

import business.save_geojson
from business.save_geojson import make_heat
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
    file_list = os.listdir(dataset_dir)
    for file in file_list:
        if file.count('dyna') > 0 and file.count("truth_dyna") == 0:
            dataset_json_path = dataset_dir + os.sep + file
    print(dataset_json_path)
    # 生成地图
    if result_json_path and dataset_json_path:
        logger.info("The result json path is: " + result_json_path)
        logger.info("The dataset json path is: " + dataset_json_path)
        map_save_path = settings.ADMIN_FRONT_HTML_PATH + dataset_file.file_name + "_" + str(task_id) + "_result.html"
        render_to_map(dataset_json_path, result_json_path, background_id, map_save_path)
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
    list_hm_pre = make_series_list(prediction, dataset_json_path)
    list_hm_tru = make_series_list(truth, dataset_json_path)
    list_hm_dif = make_series_list(dif, dataset_json_path)
    m = folium.Map(
        location=return_location(dataset_json_content),
        tiles=get_background_url(background_id),
        zoom_start=12, attr='default'
    )
    HeatMapWithTime(list_hm_pre, name='prediction').add_to(m)
    HeatMapWithTime(list_hm_tru, name='truth').add_to(m)
    HeatMapWithTime(list_hm_dif, name='difference').add_to(m)
    folium.LayerControl().add_to(m)
    logger.info("The task result file was generated successfully, html path: " + map_save_path)
    m.save(map_save_path)

def make_series_list(result, dataset_json_path):
    if result.ndim == 4:
        result = result.reshape(len(result), len(result[0]), len(result[0][0]))
    # result = result.reshape(len(result), len(result[0]), len(result[0][0]))
    count_time = len(result[0])
    geo_count = len(result[0][0])
    result = np.array(result)
    result_mean1 = result.mean(axis=0)
    heat_list = []
    for i in result_mean1:
        time_list = []
        for j in i:
            item = [j]
            time_list.append(item)
        heat_list.append(time_list)
    view_json = json.load(open(dataset_json_path, 'r'))
    for i in range(len(heat_list)):
        k = 0
        for _ in view_json['features']:
            location = business.save_geojson.return_location(_)
            # print(location)
            heat_list[i][k].insert(0, location[1])
            heat_list[i][k].insert(1, location[0])
            print(heat_list[i][k])
            k += 1
    heat_time_list = []
    for loc in range(len(heat_list[0])):
        for time in range(len(heat_list)):
            heat_time_list.append(heat_list[time][loc])
    heat_time_list = make_heat(heat_time_list)
    list_hm = []
    for i in range(count_time):
        list_item = []
        for k in range(geo_count):
            list_k = heat_time_list[k * count_time:(k + 1) * count_time]
            list_item.append(list_k[i])
        list_hm.append(list_item)
    return list_hm
