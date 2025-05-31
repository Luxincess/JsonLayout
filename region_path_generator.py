import time
from path_algorithm import ObstacleAwareLongestPath


class RegionPathGenerator:
    def __init__(self, layout_manager, region_divider, endpoint_generator):
        """初始化区域路径生成器"""
        self.layout_manager = layout_manager
        self.region_divider = region_divider
        self.endpoint_generator = endpoint_generator
        self.valid_grid = region_divider.valid_grid  # 使用region_divider中的valid_grid标记可通行区域
        self.paths = []  # 存储所有子区域的路径
        self.time_tracking = {}  # 性能监控

    def generate_all_region_paths(self, vertical_dividers, horizontal_dividers, all_endpoints):
        """为所有子区域生成路径"""
        print("开始为所有子区域生成路径...")
        start_time = time.time()

        all_vertical_dividers = [0] + vertical_dividers + [self.layout_manager.cols]

        # 为每个子区域生成路径
        for endpoint in all_endpoints:
            region = endpoint['region']
            subregion = endpoint['subregion']
            start_point = endpoint['start']
            end_point = endpoint['end']

            print(f"处理区域 {region} 的 {subregion} 子区域...")

            # 确定子区域的边界
            x_min = all_vertical_dividers[region - 1]
            x_max = all_vertical_dividers[region]

            # 找到可能的水平分隔线
            y_divider = None
            for x_start, x_end, y_pos in horizontal_dividers:
                if x_start == x_min and x_end == x_max:
                    y_divider = y_pos
                    break

            # 确定子区域的边界行
            if subregion == 'upper' and y_divider is not None:
                y_min = y_divider
                y_max = self.layout_manager.rows
            elif subregion == 'lower' and y_divider is not None:
                y_min = 0
                y_max = y_divider
            else:  # whole region
                y_min = 0
                y_max = self.layout_manager.rows

            # 生成子区域的路径
            path = self.generate_region_path(region, subregion, x_min, x_max, y_min, y_max, start_point, end_point)

            if path:
                self.paths.append({
                    'region': region,
                    'subregion': subregion,
                    'path': path
                })
                print(f"区域 {region} 的 {subregion} 子区域路径生成完成，长度为 {len(path)}")
            else:
                print(f"警告: 区域 {region} 的 {subregion} 子区域路径生成失败！")

        self.time_tracking["所有区域路径生成"] = time.time() - start_time
        print(f"所有子区域路径生成完成，总耗时: {self.time_tracking['所有区域路径生成']:.2f}秒")
        return self.paths

    def generate_region_path(self, region, subregion, x_min, x_max, y_min, y_max, start_point, end_point):
        """为指定子区域生成路径"""
        # 获取子区域的大小
        rows = int(y_max - y_min)
        cols = int(x_max - x_min)

        if rows <= 0 or cols <= 0:
            print(f"警告: 区域 {region} 的 {subregion} 子区域大小无效: rows={rows}, cols={cols}")
            return None

        # 确定子区域内的障碍物
        obstacles = []
        for i in range(int(y_min), int(y_max)):
            for j in range(int(x_min), int(x_max)):
                if i < self.layout_manager.rows and j < self.layout_manager.cols:
                    if self.valid_grid[i, j] == 0:  # 0表示不可通行区域
                        # 转换为相对于子区域的坐标
                        obstacles.append((i - int(y_min), j - int(x_min)))

        # 转换起点和终点到子区域相对坐标
        start_rel = (int(start_point[1] - y_min), int(start_point[0] - x_min))
        end_rel = (int(end_point[1] - y_min), int(end_point[0] - x_min))

        # 确保起点和终点在子区域内且不是障碍物
        if start_rel[0] < 0 or start_rel[0] >= rows or start_rel[1] < 0 or start_rel[1] >= cols:
            # 调整起点到子区域边界
            start_rel = (max(0, min(rows - 1, start_rel[0])), max(0, min(cols - 1, start_rel[1])))

        if end_rel[0] < 0 or end_rel[0] >= rows or end_rel[1] < 0 or end_rel[1] >= cols:
            # 调整终点到子区域边界
            end_rel = (max(0, min(rows - 1, end_rel[0])), max(0, min(cols - 1, end_rel[1])))

        # 确保起点和终点不在障碍物上
        if start_rel in obstacles:
            obstacles.remove(start_rel)

        if end_rel in obstacles:
            obstacles.remove(end_rel)

        # 创建路径生成器对象
        path_generator = ObstacleAwareLongestPath(rows, cols, obstacles, start_rel, end_rel)


        # 生成路径
        path = path_generator.generate_longest_path()

        # 转换回全局坐标
        global_path = []
        for i, j in path:
            global_path.append((i + int(y_min), j + int(x_min)))

        return global_path

