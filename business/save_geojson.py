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


def show_geo_view(url, json_file, file, background_id):
    geo_layer = f"{url}" + os.sep + f"{json_file}"
    view_json = json.load(open(geo_layer, 'r'))
    _ = view_json['features'][0]
    origin_location = return_location(_)
    print(origin_location)
    if origin_location is not None:
        logger.info('尝试绘制' + geo_layer + '文件的地理图象')
        print(background_id)
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
            print(feature_list)
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
            marker_cluster = MarkerCluster().add_to(m)
            print(background_url)
            #   所有可能的展示组合
            #   features_properties_traffic_speed
            #   features_properties_inflow, features_properties_outflow
            #   features_properties_length
            #   features_properties_highway
            #   features_properties_usr_id
            if 'features_properties_traffic_speed' in feature_list:
                for _ in view_json['features']:
                    location_str = return_location(_)
                    loc1 = location_str[0]
                    loc = location_str[1:]
                    loc.append(loc1)
                    heatmap = copy(loc)
                    heatmap.append(_['properties']['traffic_speed'])
                    heat.append(heatmap)
                    folium.Marker(
                        location=loc,
                        popup='mean_traffic_speed=' + str(_['properties']['traffic_speed']),
                    ).add_to(marker_cluster)
                HeatMap(heat).add_to(m)
            elif 'features_properties_inflow' and 'features_properties_outflow' in feature_list:
                for _ in view_json['features']:
                    if _['geometry']['type'] == 'MultiPolygon':
                        pass
                    else:
                        location_str = return_location(_)
                        loc1 = location_str[0]
                        loc = location_str[1:]
                        loc.append(loc1)
                        heatmap = copy(loc)
                        heatmap.append(abs(_['properties']['inflow'] - _['properties']['outflow']))
                        heat.append(heatmap)
                        folium.Marker(
                            location=loc,
                            popup='mean_net_flow=' + str(_['properties']['inflow'] - _['properties']['outflow']),
                        ).add_to(marker_cluster)
                HeatMap(heat).add_to(m)
                folium.GeoJson(geo_layer, name=f"{json_file}").add_to(m)
            elif 'features_properties_length' in feature_list:
                for _ in view_json['features']:
                    location_str = return_location(_)
                    loc1 = location_str[0]
                    loc = location_str[1:]
                    loc.append(loc1)
                    folium.Marker(
                        location=loc,
                        popup='length=' + str(_['properties']['length']),
                    ).add_to(marker_cluster)
                folium.GeoJson(geo_layer, name=f"{json_file}").add_to(m)
            elif 'features_properties_usr_id' in feature_list:
                location_str = return_location(_)
                loc1 = location_str[0]
                loc = location_str[1:]
                loc.append(loc1)
                folium.Marker(
                    location=loc,
                    popup='user_id=' + str(_['properties']['usr_id']),
                    color='crimson',
                    fill=False,
                ).add_to(m)
                folium.GeoJson(geo_layer, name=f"{json_file}").add_to(m)
            elif 'features_properties_highway' in feature_list:
                location_str = return_location(_)
                loc1 = location_str[0]
                loc = location_str[1:]
                loc.append(loc1)
                folium.Marker(
                    location=loc,
                    popup='highway=' + str(_['properties']['highway']),
                    color='crimson',
                    fill=False,
                ).add_to(m)
                folium.GeoJson(geo_layer, name=f"{json_file}").add_to(m)
            else:
                property = str(feature_list[-1]).replace('features_properties_', '')
                location_str = return_location(_)
                loc1 = location_str[0]
                loc = location_str[1:]
                loc.append(loc1)
                folium.Marker(
                    location=loc,
                    popup='property=' + str(_['properties'][f"{property}"]),
                    color='crimson',
                    fill=False,
                ).add_to(m)
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
    location = None
    if len(block['geometry']['coordinates']) > 0:
        if type(block['geometry']['coordinates'][0]) is not list:
            location = block['geometry']['coordinates']
        else:
            if type(block['geometry']['coordinates'][0][0]) is not list:
                location = block['geometry']['coordinates'][0]
            else:
                location = block['geometry']['coordinates'][0][0]
    return location


def show_data_statis(url, file):
    file_path = url.replace('_geo_json', '')
    for files in os.listdir(file_path):
        if files.count('dyna') > 0:
            logger.info('尝试绘制' + files + '文件的[dyna]统计图象')
            data = pd.read_csv(settings.DATASET_PATH + file + os.sep + files, index_col='dyna_id')
            if 'traffic_flow' in data:
                try:
                    min_value = data.entity_id.min()
                    max_value = data.entity_id.max()
                    test_dict = {'id': [], 'net_flow': []}
                    for i in data.entity_id.unique():
                        net_flow = data.traffic_flow[data.entity_id == int(i)].mean()
                        test_dict['id'].append(i)
                        test_dict['net_flow'].append(net_flow)
                        pass
                    form_statis_html(test_dict, 'net_flow', min_value, max_value, file)
                    file_view_status = DatasetStatusEnum.SUCCESS_stat.value
                except Exception:
                    file_view_status = DatasetStatusEnum.ERROR.value
                return file_view_status
            elif 'in_flow' in data and 'out_flow' in data:
                try:
                    min_value = data.entity_id.min()
                    max_value = data.entity_id.max()
                    test_dict = {'id': [], 'net_flow': []}
                    for i in data.entity_id.unique():
                        inflow = data.in_flow[data.entity_id == int(i)].mean()
                        outflow = data.out_flow[data.entity_id == int(i)].mean()
                        test_dict['id'].append(i)
                        test_dict['net_flow'].append(inflow - outflow)
                        pass
                    form_statis_html(test_dict, 'net_flow', min_value, max_value, file)
                    file_view_status = DatasetStatusEnum.SUCCESS_stat.value
                except Exception:
                    file_view_status = DatasetStatusEnum.ERROR.value
                return file_view_status
            elif 'inflow' in data and 'outflow' in data:
                try:
                    min_value = data.entity_id.min()
                    max_value = data.entity_id.max()
                    test_dict = {'id': [], 'net_flow': []}
                    for i in data.entity_id.unique():
                        inflow = data.inflow[data.entity_id == int(i)].mean()
                        outflow = data.outflow[data.entity_id == int(i)].mean()
                        test_dict['id'].append(i)
                        test_dict['net_flow'].append(inflow - outflow)
                        pass
                    form_statis_html(test_dict, 'net_flow', min_value, max_value, file)
                    file_view_status = DatasetStatusEnum.SUCCESS_stat.value
                except Exception:
                    file_view_status = DatasetStatusEnum.ERROR.value
                return file_view_status
            elif 'pickup' in data and 'dropoff' in data:
                try:
                    min_value = data.entity_id.min()
                    max_value = data.entity_id.max()
                    test_dict = {'id': [], 'net_quantity': []}
                    for i in data.entity_id.unique():
                        pickup = data.pickup[data.entity_id == int(i)].mean()
                        dropoff = data.dropoff[data.entity_id == int(i)].mean()
                        test_dict['id'].append(i)
                        test_dict['net_flow'].append(pickup - dropoff)
                        pass
                    form_statis_html(test_dict, 'net_quantity', min_value, max_value, file)
                    file_view_status = DatasetStatusEnum.SUCCESS_stat.value
                except Exception:
                    file_view_status = DatasetStatusEnum.ERROR.value
                return file_view_status
            elif 'traffic_speed' in data:
                try:
                    min_value = data.entity_id.min()
                    max_value = data.entity_id.max()
                    test_dict = {'id': [], 'traffic_speed': []}
                    for i in data.entity_id.unique():
                        net_flow = data.traffic_speed[data.entity_id == int(i)].mean()
                        test_dict['id'].append(i)
                        test_dict['traffic_speed'].append(net_flow)
                        pass
                    form_statis_html(test_dict, 'traffic_speed', min_value, max_value, file)
                    file_view_status = DatasetStatusEnum.SUCCESS_stat.value
                except Exception:
                    file_view_status = DatasetStatusEnum.ERROR.value
                return file_view_status
            elif 'traffic_intensity' in data:
                try:
                    min_value = data.entity_id.min()
                    max_value = data.entity_id.max()
                    test_dict = {'id': [], 'traffic_intensity': []}
                    for i in data.entity_id.unique():
                        net_flow = data.traffic_intensity[data.entity_id == int(i)].mean()
                        test_dict['id'].append(i)
                        test_dict['traffic_intensity'].append(net_flow)
                        pass
                    form_statis_html(test_dict, 'traffic_intensity', min_value, max_value, file)
                    file_view_status = DatasetStatusEnum.SUCCESS_stat.value
                except Exception:
                    file_view_status = DatasetStatusEnum.ERROR.value
                return file_view_status
            else:
                file_view_status = DatasetStatusEnum.ERROR.value
                return file_view_status
        if files.count('grid') > 0:
            logger.info('尝试绘制' + files + '文件的[grid]统计图象')
            data = pd.read_csv(settings.DATASET_PATH + file + '/' + files, index_col='dyna_id')
            # test_dict = {'id': [], 'inflow': [], 'outflow': [], 'net_flow': []}
            if 'risk' in data:
                try:
                    test_dict = {'id': [], 'risk': []}
                    page_legth = 0
                    for i in data.row_id.unique():
                        for j in data.column_id.unique():
                            page_legth += 1
                            risk = data.risk[data.row_id == int(i)][data.column_id == int(j)].mean()
                            test_dict['id'].append(f"{i}" + f", {j}")
                            test_dict['risk'].append(risk)
                    form_long_statis_html(test_dict, 'risk', page_legth, file)
                    file_view_status = DatasetStatusEnum.SUCCESS_stat.value
                    logger.info('统计图象绘制完成')
                except Exception:
                    file_view_status = DatasetStatusEnum.ERROR.value
                return file_view_status
            elif 'inflow' in data and 'outflow' in data:
                try:
                    test_dict = {'id': [], 'inflow': [], 'outflow': [], 'net_flow': []}
                    page_legth = 0
                    for i in data.row_id.unique():
                        for j in data.column_id.unique():
                            page_legth += 1
                            inflow = data.inflow[data.row_id == int(i)][data.column_id == int(j)].mean()
                            outflow = data.outflow[data.row_id == int(i)][data.column_id == int(j)].mean()
                            test_dict['id'].append(f'{i},' + f'{j}')
                            test_dict['inflow'].append(inflow)
                            test_dict['outflow'].append(outflow)
                            test_dict['net_flow'].append(inflow - outflow)
                            pass
                    form_long_statis_html(test_dict, 'net_flow', page_legth, file)
                    file_view_status = DatasetStatusEnum.SUCCESS_stat.value
                    logger.info('统计图象绘制完成')
                except Exception:
                    file_view_status = DatasetStatusEnum.ERROR.value
                return file_view_status
            elif 'pickup' in data and 'dropoff' in data:
                try:
                    test_dict = {'id': [], 'pickup': [], 'dropoff': [], 'net_quantity': []}
                    page_legth = 0
                    for i in data.row_id.unique():
                        for j in data.column_id.unique():
                            page_legth += 1
                            pickup = data.pickup[data.row_id == int(i)][data.column_id == int(j)].mean()
                            dropoff = data.dropoff[data.row_id == int(i)][data.column_id == int(j)].mean()
                            test_dict['id'].append(f'{i},' + f'{j}')
                            test_dict['pickup'].append(pickup)
                            test_dict['dropoff'].append(dropoff)
                            test_dict['net_quantity'].append(pickup - dropoff)
                            pass
                    form_long_statis_html(test_dict, 'net_quantity', page_legth, file)
                    file_view_status = DatasetStatusEnum.SUCCESS_stat.value
                    logger.info('统计图象绘制完成')
                except Exception:
                    file_view_status = DatasetStatusEnum.ERROR.value
                return file_view_status
            elif 'departing_volume' in data and 'arriving_volume' in data:
                try:
                    test_dict = {'id': [], 'departing_volume': [], 'arriving_volume': [], 'net_departing_volume': []}
                    page_legth = 0
                    for i in data.row_id.unique():
                        for j in data.column_id.unique():
                            page_legth += 1
                            departing_volume = data.departing_volume[data.row_id == int(i)][
                                data.column_id == int(j)].mean()
                            arriving_volume = data.arriving_volume[data.row_id == int(i)][
                                data.column_id == int(j)].mean()
                            test_dict['id'].append(f'{i},' + f'{j}')
                            test_dict['departing_volume'].append(departing_volume)
                            test_dict['arriving_volume'].append(arriving_volume)
                            test_dict['net_departing_volume'].append(departing_volume - arriving_volume)
                            pass
                    form_long_statis_html(test_dict, 'net_departing_volume', page_legth, file)
                    file_view_status = DatasetStatusEnum.SUCCESS_stat.value
                    logger.info('统计图象绘制完成')
                except Exception:
                    file_view_status = DatasetStatusEnum.ERROR.value
                return file_view_status

            else:
                file_view_status = DatasetStatusEnum.ERROR.value
                return file_view_status


def form_statis_html(test_dict, asix_y, min_value, max_value, file):
    test_dict_df = pd.DataFrame(test_dict)
    chart = alt.Chart(test_dict_df, title='Mean of ' + f"{asix_y}" + ' on timeseries').mark_point().encode(
        x=alt.X('id', scale=alt.Scale(domain=[min_value, max_value])),
        y=asix_y,
    ).properties(
        width=1000
    ).interactive()
    chart.save(settings.ADMIN_FRONT_HTML_PATH + str(file) + ".html")


def form_long_statis_html(test_dict, asix_y, page_legth, file):
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

            assert len(self.geo_file) == 1

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
                self.geo_path = self.raw_path + self.dataset + '/' + self.geo_file[0]
                self._visualize_geo()
                # dyna
                for dyna_file in self.dyna_file:
                    self.dyna_path = self.raw_path + self.dataset + '/' + dyna_file
                    self._visualize_dyna()
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
            feature_i['properties'] = feature_dct
            feature_i['geometry'] = {}
            feature_i['geometry']['type'] = row['type']
            feature_i['geometry']['coordinates'] = eval(row['coordinates'])
            geojson_obj['features'].append(feature_i)

        ensure_dir(self.save_path)
        save_name = "_".join(self.dyna_path.split('/')[-1].split('.')) + '.json'
        json.dump(geojson_obj, open(self.save_path + '/' + save_name, 'w',
                                    encoding='utf-8'),
                  ensure_ascii=False, indent=4)

    def _visualize_grid(self):
        geo_file = pd.read_csv(self.geo_path, index_col=None)
        grid_file = pd.read_csv(self.grid_path, index_col=None)
        geojson_obj = {'type': "FeatureCollection", 'features': []}

        # get feature_lst
        geo_feature_lst = [_ for _ in list(geo_file.columns) if _ not in self.geo_reserved_lst]
        grid_feature_lst = [_ for _ in list(grid_file.columns) if _ not in self.grid_reserved_lst]

        for _, row in geo_file.iterrows():

            # get feature dictionary
            row_id, column_id = row['row_id'], row['column_id']
            feature_dct = row[geo_feature_lst].to_dict()
            dyna_i = grid_file[(grid_file['row_id'] == row_id) & (grid_file['column_id'] == column_id)]
            for f in grid_feature_lst:
                feature_dct[f] = float(dyna_i[f].mean())

            # form a feature
            feature_i = dict()
            feature_i['type'] = 'Feature'
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
        trajectory = {}
        GPS_traj = "coordinates" in dyna_file.columns
        if not GPS_traj:
            geo_file = pd.read_csv(self.geo_path, index_col=None)

        a = dyna_file.groupby("entity_id")
        for entity_id, entity_value in a:
            if "traj_id" in dyna_file.columns:
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
                    if GPS_traj:
                        for _, row in traj_value.iterrows():
                            feature_i['geometry']['coordinates'].append(eval(row['coordinates']))
                    else:
                        for _, row in traj_value.iterrows():
                            coor = eval(geo_file.loc[row['location']]['coordinates'])
                            if _ == 0:
                                feature_i['geometry']['coordinates'].append(coor[0])
                            feature_i['geometry']['coordinates'].append(coor[1])
                    geojson_obj['features'].append(feature_i)

            else:
                feature_dct = {"usr_id": entity_id}
                feature_i = dict()
                feature_i['type'] = 'Feature'
                feature_i['properties'] = feature_dct
                feature_i['geometry'] = {}
                feature_i['geometry']['type'] = "LineString"
                feature_i['geometry']['coordinates'] = []
                if GPS_traj:
                    for _, row in entity_value.iterrows():
                        feature_i['geometry']['coordinates'].append(eval(row['coordinates']))
                else:
                    for _, row in entity_value.iterrows():
                        coor = eval(geo_file.loc[row['location']]['coordinates'])
                        if _ == 0:
                            feature_i['geometry']['coordinates'].append(coor[0])
                        feature_i['geometry']['coordinates'].append(coor[1])
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
    try:
        helper = VisHelper(dataset, save_path)
        file_form_status = helper.visualize()
        return file_form_status
    except Exception:
        file_form_status = DatasetStatusEnum.ERROR.value
        print(file_form_status)
        return file_form_status
