from copy import copy

import folium
import pandas as pd
import json
import os
import altair as alt
from django.conf import settings
from folium.plugins import HeatMap, MarkerCluster

from business.enums import DatasetStatusEnum
from common.utils import get_json_features
from loguru import logger
from sklearn import preprocessing
import numpy as np


def transfer_geo_json(url, file, background_id):
    """
    通过文件路径获取geojson文件，根据文件的类型进行可视化
    """
    for json_file in os.listdir(url):
        if json_file.count('dyna') > 0:
            if json_file.count('_truth_dyna') > 0:
                pass
            else:
                file_view_status = show_geo_view(url, json_file, file, background_id)
                return file_view_status
        elif json_file.count('grid') > 0:
            file_view_status = show_geo_view(url, json_file, file, background_id)
            return file_view_status
        elif json_file.count('geo') > 0:
            file_view_status = show_geo_view(url, json_file, file, background_id)
            return file_view_status
        else:
            file_view_status = show_data_statis(url, file)
            return file_view_status


def make_map_only(_, heat, marker_cluster, tag, mean_or_not=True):
    location_str = return_location(_)
    loc1 = location_str[0]
    loc = location_str[1:]
    loc.append(loc1)
    heatmap = copy(loc)
    heatmap.append(_['properties'][tag])
    heat.append(heatmap)
    if mean_or_not:
        folium.Marker(
            location=loc,
            popup='mean ' + tag + '=' + str(_['properties'][tag]),
        ).add_to(marker_cluster)
    else:
        folium.Marker(
            location=loc,
            popup=tag + '=' + str(_['properties'][tag]),
        ).add_to(marker_cluster)


def make_map_double(_, heat, marker_cluster, tag1, tag2, mean_or_not=True):
    location_str = return_location(_)
    loc1 = location_str[0]
    loc = location_str[1:]
    loc.append(loc1)
    heatmap = copy(loc)
    heatmap.append(abs(_['properties'][tag1] + _['properties'][tag2]))
    heat.append(heatmap)
    if mean_or_not:
        folium.Marker(
            location=loc,
            popup=tag1 + '+' + tag2 + '=' + str(_['properties'][tag1] + _['properties'][tag2]),
        ).add_to(marker_cluster)
    else:
        folium.Marker(
            location=loc,
            popup=tag1 + '+' + tag2 + '=' + str(_['properties'][tag1] + _['properties'][tag2]),
        ).add_to(marker_cluster)


def make_heat(heat):
    """
    为热力图数据进行归一化处理
    """
    np_heat = np.array(heat[:])
    heat_value = np_heat[:, -1]
    i = 0
    for item in heat_value:
        heat_value[i] = abs(item)
        i += 1
    min_max_scaler = preprocessing.MinMaxScaler()
    X_minMax = min_max_scaler.fit_transform(heat_value.reshape(-1, 1))
    i = 0
    for item in X_minMax:
        np_heat[i, -1] = item[0]
        i += 1
    heat = np_heat.tolist()
    return heat


def make_Choropleth_csv(view_json, file, url, tag1=None, tag2=None):
    csv_raw_data = []
    if tag2 is None:
        tag_name = tag1
        i=0
        for _ in view_json['features']:
            geo_id = _['properties']['geo_id']
            tag_value = _['properties'][tag1]
            csv_raw_data.append([geo_id, tag_value])
            i += 1
    else:
        tag_name = 'sum_'+tag1+'_'+tag2
        i = 0
        for _ in view_json['features']:
            geo_id = _['properties']['geo_id']
            tag_value = _['properties'][tag1]+_['properties'][tag2]
            csv_raw_data.append([geo_id, tag_value])
            i += 1
    csv_column_name = ['geo_id', tag_name]
    csv_pd = pd.DataFrame(columns=csv_column_name,data=csv_raw_data)
    csv_path = f"{url}" + os.sep + f"{file}" + '.csv'
    csv_pd.to_csv(csv_path,index=False)
    return csv_path


def add_Choropleth(csv_url, m, state_geo, tag1=None, tag2=None,name="choropleth"):
    Choropleth_data = pd.read_csv(csv_url)
    if tag2 is None:
        print('choose 1')
        folium.Choropleth(
            geo_data=state_geo,
            name=name,
            data=Choropleth_data,
            columns=["geo_id", tag1],
            key_on="feature.id",
            fill_color="YlGn",
            fill_opacity=0.7,
            line_opacity=0.2,
            legend_name="Unemployment Rate (%)",
        ).add_to(m)
    else:
        folium.Choropleth(
            geo_data=state_geo,
            name=name,
            data=Choropleth_data,
            columns=["geo_id", 'sum_'+tag1+'_'+tag2],
            key_on="feature.id",
            fill_color="YlGn",
            fill_opacity=0.7,
            line_opacity=0.2,
            legend_name='sum_'+tag1+'_'+tag2,
        ).add_to(m)


def show_geo_view(url, json_file, file, background_id):
    """
    解析json文件并按照不同的展示规则进行展示
    """
    geo_layer = f"{url}" + os.sep + f"{json_file}"
    view_json = json.load(open(geo_layer, 'r'))
    _ = view_json['features'][0]
    origin_location = return_location(_)
    if origin_location is not None:
        logger.info('尝试绘制' + geo_layer + '文件的地理图象')
        if int(background_id) == 1:
            background_url = 'https://mt.google.com/vt/lyrs=m&x={x}&y={y}&z={z}'
        elif int(background_id) == 2:
            background_url = 'https://mt.google.com/vt/lyrs=s&x={x}&y={y}&z={z}'
        elif int(background_id) == 3:
            background_url = 'https://webrd02.is.autonavi.com/appmaptile?lang=zh_en&size=1&scale=1&style=8&x={' \
                             'x}&y={y}&z={z} '
        elif int(background_id) == 4:
            background_url = 'http://webst02.is.autonavi.com/appmaptile?style=6&x={x}&y={y}&z={z}'
        elif int(background_id) == 5:
            background_url = 'OpenStreetMap'
        elif int(background_id) == 6:
            background_url = 'https://tileserver.memomaps.de/tilegen/{z}/{x}/{y}.png'
        elif int(background_id) == 7:
            background_url = 'https://stamen-tiles-{s}.a.ssl.fastly.net/toner-hybrid/{z}/{x}/{y}{r}.png'
        else:
            background_url = 'https://mt.google.com/vt/lyrs=m&x={x}&y={y}&z={z}'
        try:
            feature_list = get_json_features(geo_layer)
            # logger.info('json文件的可标记属性' + feature_list)
            loc1 = origin_location[0]
            loc = origin_location[1:]
            loc.append(loc1)
            heat = []
            m = folium.Map(
                location=loc,
                tiles=background_url,
                zoom_start=12, attr='default'
            )
            marker_cluster = MarkerCluster(name='Cluster').add_to(m)
            print(background_url)
            #   所有可能的展示组合
            #   features_properties_traffic_speed
            #   features_properties_inflow, features_properties_outflow
            #   features_properties_length
            #   features_properties_highway
            #   features_properties_usr_id
            #   (last property in list)
            if 'features_properties_traffic_speed' in feature_list:
                for _ in view_json['features']:
                    make_map_only(_, heat, marker_cluster, tag='traffic_speed')
                heat_minmax = make_heat(heat)
                HeatMap(heat_minmax, name='traffic_speed_heatmap').add_to(m)
            elif 'features_properties_inflow' and 'features_properties_outflow' in feature_list:
                for _ in view_json['features']:
                    if _['geometry']['type'] == 'MultiPolygon':
                        pass
                    else:
                        make_map_double(_, heat, marker_cluster, tag1='inflow', tag2='outflow')
                heat_minmax = make_heat(heat)
                csv_url = make_Choropleth_csv(view_json, file, url, tag1='inflow',tag2='outflow')
                try:
                    add_Choropleth(csv_url, m, state_geo=geo_layer, tag1='inflow',tag2='outflow',name='Cor')
                except Exception:
                    pass
                HeatMap(heat_minmax,name='abs_flow_heatmap').add_to(m)
                folium.GeoJson(geo_layer, name=f"{json_file}", tooltip=f"{json_file}").add_to(m)

            elif 'features_properties_length' in feature_list:
                for _ in view_json['features']:
                    make_map_only(_, heat, marker_cluster, 'length', mean_or_not=False)
                folium.GeoJson(geo_layer, name=f"{json_file}").add_to(m)
            elif 'features_properties_traj_id' in feature_list:
                for _ in view_json['features']:
                    make_map_only(_, heat, marker_cluster, 'traj_id', mean_or_not=False)
                folium.GeoJson(geo_layer, name=f"{json_file}").add_to(m)
            elif 'features_properties_usr_id' in feature_list:
                for _ in view_json['features']:
                    make_map_only(_, heat, marker_cluster, 'usr_id', mean_or_not=False)
                folium.GeoJson(geo_layer, name=f"{json_file}").add_to(m)
            elif 'features_properties_highway' in feature_list:
                for _ in view_json['features']:
                    make_map_only(_, heat, marker_cluster, 'highway', mean_or_not=False)
                folium.GeoJson(geo_layer, name=f"{json_file}").add_to(m)
            else:
                property = str(feature_list[-1]).replace('features_properties_', '')
                for _ in view_json['features']:
                    make_map_only(_, heat, marker_cluster, property, mean_or_not=False)
                folium.GeoJson(geo_layer, name=f"{json_file}").add_to(m)
            # add data point to the mark cluster
            folium.LayerControl().add_to(m)
            geo_view_path = settings.ADMIN_FRONT_HTML_PATH + str(file) + ".html"
            m.save(geo_view_path)
            file_view_status = DatasetStatusEnum.SUCCESS.value
            logger.info(geo_layer + '文件的地理图象绘制成功')
        except Exception:
            file_view_status = show_data_statis(url, file)
    else:
        file_view_status = show_data_statis(url, file)
    return file_view_status


def return_location(block):
    """
    获取一个feature的geometry-coordinates内容并按照它是点线面来返回其定位坐标点
    """
    location = None
    if len(block['geometry']['coordinates']) > 0:
        if type(block['geometry']['coordinates'][0]) is not list:
            location = block['geometry']['coordinates']
        else:
            if type(block['geometry']['coordinates'][0][0]) is not list:
                location = block['geometry']['coordinates'][0]
            else:
                if type(block['geometry']['coordinates'][0][0][0]) is not list:
                    location = block['geometry']['coordinates'][0][0]
                else:
                    location = block['geometry']['coordinates'][0][0][0]
    return location


def make_statis_only(data, file, tag, name, grid=False):
    """
    利用只有一个参数，获取统计图象
    """
    if not grid:
        try:
            min_value = data.entity_id.min()
            max_value = data.entity_id.max()
            test_dict = {'id': [], name: []}
            for i in data.entity_id.unique():
                tag_value = getattr(data, tag)[data.entity_id == int(i)].mean()
                test_dict['id'].append(i)
                test_dict[name].append(tag_value)
                pass
            form_statis_html(test_dict, name, min_value, max_value, file)
            file_view_status = DatasetStatusEnum.SUCCESS_stat.value
        except Exception:
            file_view_status = DatasetStatusEnum.ERROR.value
    else:
        try:
            test_dict = {'id': [], name: []}
            page_legth = 0
            for i in data.row_id.unique():
                for j in data.column_id.unique():
                    page_legth += 1
                    tag_value = getattr(data, tag)[data.row_id == int(i)][data.column_id == int(j)].mean()
                    test_dict['id'].append(f"{i}" + f", {j}")
                    test_dict[name].append(tag_value)
            form_long_statis_html(test_dict, name, page_legth, file)
            file_view_status = DatasetStatusEnum.SUCCESS_stat.value
            logger.info('统计图象绘制完成')
        except Exception:
            file_view_status = DatasetStatusEnum.ERROR.value
    return file_view_status


def make_statis_double(data, file, tag1, tag2, name, grid=False):
    if not grid:
        try:
            min_value = data.entity_id.min()
            max_value = data.entity_id.max()
            test_dict = {'id': [], name: []}
            for i in data.entity_id.unique():
                tag1_value = getattr(data, tag1)[data.entity_id == int(i)].mean()
                tag2_value = getattr(data, tag2)[data.entity_id == int(i)].mean()
                test_dict['id'].append(i)
                test_dict[name].append(tag1_value + tag2_value)
                pass
            form_statis_html(test_dict, name, min_value, max_value, file)
            file_view_status = DatasetStatusEnum.SUCCESS_stat.value
        except Exception:
            file_view_status = DatasetStatusEnum.ERROR.value
    else:
        try:
            test_dict = {'id': [], name: []}
            page_legth = 0
            for i in data.row_id.unique():
                for j in data.column_id.unique():
                    page_legth += 1
                    tag1_value = getattr(data, tag1)[data.row_id == int(i)][data.column_id == int(j)].mean()
                    tag2_value = getattr(data, tag2)[data.row_id == int(i)][data.column_id == int(j)].mean()
                    test_dict['id'].append(f'{i},' + f'{j}')
                    test_dict[name].append(tag1_value - tag2_value)
                    pass
            form_long_statis_html(test_dict, name, page_legth, file)
            file_view_status = DatasetStatusEnum.SUCCESS_stat.value
            logger.info('统计图象绘制完成')
        except Exception:
            file_view_status = DatasetStatusEnum.ERROR.value
    return file_view_status


def show_data_statis(url, file):
    """
    如果无法展示其地理图象则将其描述性统计数据展示
    """
    file_path = url.replace('_geo_json', '')
    for files in os.listdir(file_path):
        if files.count('dyna') > 0:
            logger.info('尝试绘制' + files + '文件的[dyna]统计图象')
            data = pd.read_csv(settings.DATASET_PATH + file + os.sep + files, index_col='dyna_id')
            if 'traffic_flow' in data:
                file_view_status = make_statis_only(data, file, tag='traffic_flow', name='abs_traffic_flow')
                return file_view_status
            elif 'in_flow' in data and 'out_flow' in data:
                file_view_status = make_statis_double(data, file, 'in_flow', 'out_flow', 'abs_flow')
                return file_view_status
            elif 'inflow' in data and 'outflow' in data:
                file_view_status = make_statis_double(data, file, 'inflow', 'outflow', 'abs_flow')
                return file_view_status
            elif 'pickup' in data and 'dropoff' in data:
                file_view_status = make_statis_double(data, file, 'pickup', 'dropoff', 'abs_quantity')
                return file_view_status
            elif 'traffic_speed' in data:
                file_view_status = make_statis_only(data, file, tag='traffic_speed', name='traffic_speed')
                return file_view_status
            elif 'traffic_intensity' in data:
                file_view_status = make_statis_only(data, file, tag='traffic_intensity', name='traffic_intensity')
                return file_view_status
            else:
                file_view_status = DatasetStatusEnum.ERROR.value
                return file_view_status
        if files.count('grid') > 0:
            logger.info('尝试绘制' + files + '文件的[grid]统计图象')
            data = pd.read_csv(settings.DATASET_PATH + file + '/' + files, index_col='dyna_id')
            # test_dict = {'id': [], 'inflow': [], 'outflow': [], 'abs_flow': []}
            if 'risk' in data:
                file_view_status = make_statis_only(data, file, tag='risk', name='risk', grid=True)
                return file_view_status
            elif 'inflow' in data and 'outflow' in data:
                file_view_status = make_statis_double(data, file, 'inflow', 'outflow', 'abs_flow', grid=True)
                return file_view_status
            elif 'pickup' in data and 'dropoff' in data:
                file_view_status = make_statis_double(data, file, 'pickup', 'dropoff', 'abs_quantity', grid=True)
                return file_view_status
            elif 'departing_volume' in data and 'arriving_volume' in data:
                file_view_status = make_statis_double(data, file, 'departing_volume', 'arriving_volume', 'abs_volume',
                                                      grid=True)
                return file_view_status
            else:
                file_view_status = DatasetStatusEnum.ERROR.value
                return file_view_status


def form_statis_html(test_dict, asix_y, min_value, max_value, file):
    """
    根据统计数据形成一个固定宽度的html页面
    """
    test_dict_df = pd.DataFrame(test_dict)
    chart = alt.Chart(test_dict_df, title='Mean of ' + f"{asix_y}" + ' on timeseries').mark_point().encode(
        x=alt.X('id', scale=alt.Scale(domain=[min_value, max_value])),
        y=asix_y,
    ).properties(
        width=1000
    ).interactive()
    chart.save(settings.ADMIN_FRONT_HTML_PATH + str(file) + ".html")


def form_long_statis_html(test_dict, asix_y, page_legth, file):
    """
    根据统计数据形成一个可变宽度的html页面
    """
    test_dict_df = pd.DataFrame(test_dict)
    interval = alt.selection_interval()
    chart = alt.Chart(test_dict_df, title='Mean of ' + f"{asix_y}" + ' on timeseries').mark_point().encode(
        x='id',
        y=asix_y,
    ).properties(
        selection=interval,
        width=page_legth * 20
    )
    chart.save(settings.ADMIN_FRONT_HTML_PATH + str(file) + ".html")



class VisHelper:
    def __init__(self, dataset, save_path):
        try:
            self.raw_path = settings.DATASET_PATH
            self.dataset = dataset
            self.save_path = save_path
            self.file_form_status = DatasetStatusEnum.ERROR.value
            # get type
            self.config_path = self.raw_path + self.dataset + os.sep + 'config.json'
            self.data_config = json.load(open(self.config_path, 'r'))
            if 'dyna' in self.data_config and ['state'] == self.data_config['dyna']['including_types']:
                self.type = 'state'
            elif 'grid' in self.data_config and ['state'] == self.data_config['grid']['including_types']:
                self.type = 'grid'
            else:
                self.type = 'trajectory'
            # get geo and dyna files
            all_files = os.listdir(self.raw_path + self.dataset)
            self.geo_file = []
            self.geo_path = None
            self.dyna_file = []
            self.dyna_path = None
            self.grid_file = []
            self.grid_path = None
            for file in all_files:
                if file.split('.')[1] == 'geo':
                    self.geo_file.append(file)
                if file.split('.')[1] == 'dyna':
                    self.dyna_file.append(file)
                if file.split('.')[1] == 'grid':
                    self.grid_file.append(file)
            try:
                assert len(self.geo_file) == 1
            except Exception:
                pass

            # reserved columns
            self.geo_reserved_lst = ['type', 'coordinates']
            self.dyna_reserved_lst = ['dyna_id', 'type', 'time', 'entity_id', 'traj_id', 'coordinates']
            self.grid_reserved_lst = ['dyna_id', 'type', 'time', 'row_id', 'column_id']
        except Exception:
            pass

    def visualize(self):
        try:
            if self.type == 'trajectory':
                # geo
                try:
                    self.geo_path = self.raw_path + self.dataset + '/' + self.geo_file[0]
                except Exception:
                    pass
                try:
                    self._visualize_geo()
                except Exception:
                    pass
                # dyna
                for dyna_file in self.dyna_file:
                    try:
                        self.dyna_path = self.raw_path + self.dataset + '/' + dyna_file
                        self._visualize_dyna()
                    except Exception:
                        pass
            elif self.type == 'state':
                self.geo_path = self.raw_path + self.dataset + '/' + self.geo_file[0]
                for dyna_file in self.dyna_file:
                    self.dyna_path = self.raw_path + self.dataset + '/' + dyna_file
                    self._visualize_state()
            elif self.type == 'grid':
                self.geo_path = self.raw_path + self.dataset + '/' + self.geo_file[0]
                for grid_file in self.grid_file:
                    self.grid_path = self.raw_path + self.dataset + '/' + grid_file
                    self._visualize_grid()
            self.file_form_status = DatasetStatusEnum.PROCESSING_COMPLETE.value
            return self.file_form_status
        except Warning:
            return self.file_form_status

    def _visualize_state(self):
        geo_file = pd.read_csv(self.geo_path, index_col=None)
        dyna_file = pd.read_csv(self.dyna_path, index_col=None)
        geojson_obj = {'type': "FeatureCollection", 'features': []}

        # get feature_lst
        geo_feature_lst = [_ for _ in list(geo_file.columns) if _ not in self.geo_reserved_lst]
        dyna_feature_lst = [_ for _ in list(dyna_file.columns) if _ not in self.dyna_reserved_lst]

        geojson_obj = self._visualize_state_normal(geo_file,dyna_file,geo_feature_lst,dyna_feature_lst,geojson_obj)
        ensure_dir(self.save_path)
        save_name = "_".join(self.dyna_path.split('/')[-1].split('.')) + '.json'
        json.dump(geojson_obj, open(self.save_path + '/' + save_name, 'w',
                                    encoding='utf-8'),
                  ensure_ascii=False, indent=4)
    def _visualize_state_normal(self,geo_file,dyna_file,geo_feature_lst,dyna_feature_lst,geojson_obj):
        for _, row in geo_file.iterrows():
            # get feature dictionary
            geo_id = row['geo_id']
            feature_dct = row[geo_feature_lst].to_dict()
            dyna_i = dyna_file[dyna_file['entity_id'] == geo_id]
            for f in dyna_feature_lst:
                feature_dct[f] = float(dyna_i[f].mean())

            # form a feature
            feature_i = dict()
            feature_i['type'] = 'Feature'
            feature_i['id'] = geo_id
            feature_i['properties'] = feature_dct
            feature_i['geometry'] = {}
            feature_i['geometry']['type'] = row['type']
            feature_i['geometry']['coordinates'] = eval(row['coordinates'])
            geojson_obj['features'].append(feature_i)
        return geojson_obj
    def _visualize_state_time(self,geo_file,dyna_file,geo_feature_lst,dyna_feature_lst,geojson_obj):
        count_geo = dyna_file.shape[0]
        time_count = 0
        print(dyna_file.isnull().sum())
        length = geo_file.shape[0]
        for _, row in geo_file.iterrows():

            # get feature dictionary
            geo_id = row['geo_id']
            feature_dct = row[geo_feature_lst].to_dict()
            # print(feature_dct)
            dyna_i = dyna_file[dyna_file['entity_id'] == geo_id]
            # for f in dyna_feature_lst:
            #     feature_dct[f] = dyna_i[f]
            # 以下为测试热力图
            listi = []

            for f in dyna_feature_lst:
                time_count = dyna_i[f].size
                batch = int(time_count // 50)
                for i in range(50):
                    feature_dct[f] = float(dyna_i[f][i * batch:(i + 1) * batch].mean())
                    # for item in feature_dct[f]:
                    feature_dcti = row[geo_feature_lst].to_dict()
                    feature_dcti[f] = feature_dct[f] / 100
                    # 处理为0-1的数值
                    # print(feature_dcti[f])
                    listi.append(feature_dcti[f])
                    feature_i = dict()
                    feature_i['type'] = 'Feature'
                    feature_i['properties'] = feature_dcti
                    feature_i['geometry'] = {}
                    feature_i['geometry']['type'] = row['type']
                    feature_i['geometry']['coordinates'] = eval(row['coordinates'])
                    # print(feature_i)
                    geojson_obj['features'].append(feature_i)
        return geojson_obj
    def _visualize_grid(self):
        geo_file = pd.read_csv(self.geo_path, index_col=None)
        grid_file = pd.read_csv(self.grid_path, index_col=None)
        geojson_obj = {'type': "FeatureCollection", 'features': []}

        # get feature_lst
        geo_feature_lst = [_ for _ in list(geo_file.columns) if _ not in self.geo_reserved_lst]
        grid_feature_lst = [_ for _ in list(grid_file.columns) if _ not in self.grid_reserved_lst]

        for _, row in geo_file.iterrows():
            geo_id = row['geo_id']
            # get feature dictionary
            row_id, column_id = row['row_id'], row['column_id']
            feature_dct = row[geo_feature_lst].to_dict()
            dyna_i = grid_file[(grid_file['row_id'] == row_id) & (grid_file['column_id'] == column_id)]
            for f in grid_feature_lst:
                feature_dct[f] = float(dyna_i[f].mean())

            # form a feature
            feature_i = dict()
            feature_i['type'] = 'Feature'
            feature_i['id'] = geo_id
            feature_i['properties'] = feature_dct
            feature_i['geometry'] = {}
            feature_i['geometry']['type'] = row['type']
            feature_i['geometry']['coordinates'] = eval(row['coordinates'])
            geojson_obj['features'].append(feature_i)

        ensure_dir(self.save_path)
        save_name = "_".join(self.grid_path.split('/')[-1].split('.')) + '.json'
        json.dump(geojson_obj, open(self.save_path + '/' + save_name, 'w',
                                    encoding='utf-8'),
                  ensure_ascii=False, indent=4)

    def _visualize_geo(self):
        geo_file = pd.read_csv(self.geo_path, index_col=None)
        geojson_obj = {'type': "FeatureCollection", 'features': []}
        extra_feature = [_ for _ in list(geo_file.columns) if _ not in self.geo_reserved_lst]
        for _, row in geo_file.iterrows():
            feature_dct = row[extra_feature].to_dict()
            feature_i = dict()
            feature_i['type'] = 'Feature'
            feature_i['properties'] = feature_dct
            feature_i['geometry'] = {}
            feature_i['geometry']['type'] = row['type']
            feature_i['geometry']['coordinates'] = eval(row['coordinates'])
            geojson_obj['features'].append(feature_i)

        ensure_dir(self.save_path)
        save_name = "_".join(self.geo_path.split('/')[-1].split('.')) + '.json'
        json.dump(geojson_obj, open(self.save_path + '/' + save_name, 'w',
                                    encoding='utf-8'),
                  ensure_ascii=False, indent=4)

    def _visualize_dyna(self):
        dyna_file = pd.read_csv(self.dyna_path, index_col=None)

        dyna_feature_lst = [_ for _ in list(dyna_file.columns) if _ not in self.dyna_reserved_lst]
        geojson_obj = {'type': "FeatureCollection", 'features': []}
        GPS_traj = "coordinates" in dyna_file.columns
        if self.geo_path is not None:
            geo_file = pd.read_csv(self.geo_path, index_col=None)

        a = dyna_file.groupby("entity_id")
        if not GPS_traj:
            i = 0
            for entity_id, entity_value in a:
                if i < 3:
                    feature_dct = {"usr_id": entity_id}
                    feature_i = dict()
                    feature_i['type'] = 'Feature'
                    feature_i['properties'] = feature_dct
                    feature_i['geometry'] = {}
                    feature_i['geometry']['type'] = "LineString"
                    feature_i['geometry']['coordinates'] = []
                    for _, row in entity_value.iterrows():
                        coor = eval(geo_file.loc[row['location']]['coordinates'])
                        feature_i['geometry']['coordinates'].append(coor)
                    i += 1
                else:
                    break
                geojson_obj['features'].append(feature_i)
        else:
            if "traj_id" in dyna_file.columns:
                trajectory = {}
                i = 0
                for entity_id, entity_value in a:
                    if i < 3:
                        trajectory[entity_id] = {}
                        entity_value = entity_value.groupby("traj_id")
                        for traj_id, traj_value in entity_value:
                            feature_dct = {"usr_id": entity_id, "traj_id": traj_id}
                            for f in dyna_feature_lst:
                                feature_dct[f] = float(traj_value[f].mean())
                            feature_i = dict()
                            feature_i['type'] = 'Feature'
                            feature_i['properties'] = feature_dct
                            feature_i['geometry'] = {}
                            feature_i['geometry']['type'] = "LineString"
                            feature_i['geometry']['coordinates'] = []
                            for _, row in traj_value.iterrows():
                                feature_i['geometry']['coordinates'].append(eval(row['coordinates']))
                            geojson_obj['features'].append(feature_i)
                            i += 1
                    else:
                        break

            else:
                for entity_id, entity_value in a:
                    feature_i = dict()
                    feature_dct = {"usr_id": entity_id}
                    feature_i = dict()
                    feature_i['type'] = 'Feature'
                    feature_i['properties'] = feature_dct
                    feature_i['geometry'] = {}
                    feature_i['geometry']['type'] = "LineString"
                    feature_i['geometry']['coordinates'] = []
                    for _, row in entity_value.iterrows():
                        feature_i['geometry']['coordinates'].append(eval(row['coordinates']))
                    geojson_obj['features'].append(feature_i)
        ensure_dir(self.save_path)
        save_name = "_".join(self.dyna_path.split('/')[-1].split('.')) + '.json'
        json.dump(geojson_obj, open(self.save_path + '/' + save_name, 'w',
                                    encoding='utf-8'),
                  ensure_ascii=False, indent=4)


def ensure_dir(dir_path):
    """Make sure the directory exists, if it does not exist, create it.

    Args:
        dir_path (str): directory path
    """
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)


def get_geo_json(dataset, save_path):
    """
    生成geojson文件
    """
    try:
        helper = VisHelper(dataset, save_path)
        file_form_status = helper.visualize()
        return file_form_status
    except Exception:
        file_form_status = DatasetStatusEnum.ERROR.value
        print('file_form_status',file_form_status)
        return file_form_status
