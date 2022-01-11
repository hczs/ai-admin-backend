from enum import Enum


class TaskEnum(Enum):
    """
    任务类型枚举类
    """
    TRAFFIC_STATE_PRED = 'traffic_state_pred'  # 交通状态预测
    TRAJ_LOC_PRED = 'traj_loc_pred'  # 轨迹下一跳预测
    ROAD_REPRESENTATION = 'road_representation'  # 路网表征学习
    ETA = 'eta'  # 到达时间估计
    MAP_MATCHING = 'map_matching'  # 路网匹配


class TaskStatusEnum(Enum):
    """
    任务状态枚举类
    """
    NOT_STARTED = 0
    IN_PROGRESS = 1
    COMPLETED = 2
    ERROR = -1


class DatasetStatusEnum(Enum):
    """
    数据集状态枚举类
    """
    PROCESSING = 0
    PROCESSING_COMPLETE = 1  # 用来表示完成geojson文件生成
    ERROR = -1
    SUCCESS = 2  # 用来表示完成html文件生成
