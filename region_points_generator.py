from shapely.geometry import LineString, Point


class PathEndpointGenerator:
    def __init__(self, layout_manager, region_divider):
        """初始化路径端点生成器"""
        self.layout_manager = layout_manager
        self.region_divider = region_divider
        self.boundary_line = self.create_boundary_line()

    def create_boundary_line(self):
        """创建边界线的LineString对象"""
        boundary_points = self.layout_manager.get_boundary_points()
        return LineString(boundary_points)

    def find_intersection_points(self, divider_x, y_min=0, y_max=None):
        """寻找垂直分隔线与边界的交点"""
        if y_max is None:
            y_max = self.layout_manager.rows

        # 创建一条垂直分隔线
        vertical_line = LineString([(divider_x, y_min), (divider_x, y_max)])

        # 计算与边界的交点
        intersection = vertical_line.intersection(self.boundary_line)

        # 处理不同类型的交点结果
        points = []
        if intersection.is_empty:
            return points
        elif isinstance(intersection, Point):
            points.append((intersection.x, intersection.y))
        else:
            # 可能是多点集合
            try:
                for point in intersection.geoms:
                    points.append((point.x, point.y))
            except:
                # 如果不是集合，则尝试直接获取点坐标
                try:
                    points.append((intersection.x, intersection.y))
                except:
                    pass

        # 修改点: 调整非整网格的交点，向内取一格
        adjusted_points = []
        for x, y in points:
            # 检查y是否为整数
            if y == int(y):
                adjusted_y = y
            else:
                # 根据情况，如果在上方则向下取整，下方则向上取整
                if y > self.layout_manager.rows / 2:
                    adjusted_y = int(y)  # 向下取整
                else:
                    adjusted_y = int(y) + 1  # 向上取整

            adjusted_points.append((x, adjusted_y))

        return adjusted_points

    def find_horizontal_intersection_points(self, y_pos, x_min, x_max):
        """寻找水平分隔线与边界的交点"""
        # 创建水平分隔线
        horizontal_line = LineString([(x_min, y_pos), (x_max, y_pos)])

        # 与边界的交点
        boundary_intersection = horizontal_line.intersection(self.boundary_line)

        # 处理不同类型的交点结果
        boundary_points = []
        if not boundary_intersection.is_empty:
            if isinstance(boundary_intersection, Point):
                boundary_points.append((boundary_intersection.x, boundary_intersection.y))
            else:
                try:
                    for point in boundary_intersection.geoms:
                        boundary_points.append((point.x, point.y))
                except:
                    try:
                        boundary_points.append((boundary_intersection.x, boundary_intersection.y))
                    except:
                        pass

        # 修改点: 调整非整网格的交点，向内取一格
        adjusted_boundary_points = []
        for x, y in boundary_points:
            # 检查x是否为整数
            if x == int(x):
                adjusted_x = x
            else:
                # 向内部调整一格
                if x > x_min + (x_max - x_min) / 2:
                    adjusted_x = int(x)  # 向左取整
                else:
                    adjusted_x = int(x) + 1  # 向右取整

            adjusted_boundary_points.append((adjusted_x, y))

        return adjusted_boundary_points

    def generate_endpoints_for_all_regions(self, vertical_dividers, horizontal_dividers):
        """为所有区域生成路径端点"""
        all_vertical_dividers = [0] + vertical_dividers + [self.layout_manager.cols]

        # 创建字典记录水平分隔线
        h_divider_dict = {}
        for x_min, x_max, y_pos in horizontal_dividers:
            h_divider_dict[(x_min, x_max)] = y_pos

        all_endpoints = []

        # 处理每个垂直分隔区域
        for i in range(len(all_vertical_dividers) - 1):
            x_min = all_vertical_dividers[i]
            x_max = all_vertical_dividers[i + 1]
            region_num = i + 1

            # 找到该区域左右两条垂直分隔线与边界的交点
            left_intersections = self.find_intersection_points(x_min)
            right_intersections = self.find_intersection_points(x_max)

            # 检查该区域是否有水平分隔线
            if (x_min, x_max) in h_divider_dict:
                y_pos = h_divider_dict[(x_min, x_max)]

                # 寻找水平分隔线与边界的交点
                horizontal_boundary_intersections = self.find_horizontal_intersection_points(y_pos, x_min, x_max)

                # 准备上下区域的端点
                upper_start, upper_end = None, None
                lower_start, lower_end = None, None

                if region_num == 1:  # 区域1的特殊处理: 左侧为特殊边界
                    # 查找水平分隔线与边界的交点
                    if horizontal_boundary_intersections:
                        # 如果水平线与边界有交点，用它作为上下区域共享的起点
                        boundary_point = horizontal_boundary_intersections[0]  # 应该只有一个
                        upper_start = lower_start = boundary_point
                    else:
                        # 如果没有交点（罕见情况），使用左侧分隔线的一个交点
                        if left_intersections:
                            upper_start = lower_start = left_intersections[0]
                        else:
                            # 最后手段 - 使用推断坐标
                            upper_start = lower_start = (x_min, 7.0)  # 估计值

                    # 上部区域终点：右侧分隔线上方的交点
                    upper_right = [p for p in right_intersections if p[1] >= y_pos]
                    if upper_right:
                        upper_end = max(upper_right, key=lambda p: p[1])
                    else:
                        # 右侧没有上方交点，使用右分隔线与顶部的交点
                        upper_end = (x_max, max([p[1] for p in right_intersections]) if right_intersections else 15.6)

                    # 下部区域终点：右侧分隔线下方的交点
                    lower_right = [p for p in right_intersections if p[1] <= y_pos]
                    if lower_right:
                        lower_end = min(lower_right, key=lambda p: p[1])
                    else:
                        lower_end = (x_max, 0.0)  # 默认到底部边界

                elif region_num == 5:  # 区域5的特殊处理: 右侧为特殊边界
                    # 查找水平分隔线与边界的交点
                    if horizontal_boundary_intersections:
                        # 如果水平线与边界有交点，用它作为上下区域共享的终点
                        boundary_point = horizontal_boundary_intersections[0]  # 应该只有一个
                        upper_end = lower_start = boundary_point
                    else:
                        # 如果没有交点（罕见情况），使用右侧分隔线的一个交点
                        if right_intersections:
                            upper_end = lower_start = right_intersections[0]
                        else:
                            # 最后手段 - 使用推断坐标
                            upper_end = lower_start = (x_max, 11.0)  # 估计值

                    # 上部区域起点：左侧分隔线上方的交点
                    upper_left = [p for p in left_intersections if p[1] >= y_pos]
                    if upper_left:
                        upper_start = max(upper_left, key=lambda p: p[1])
                    else:
                        upper_start = (x_min, 24.0)  # 默认到顶部边界

                    # 下部区域终点：左侧分隔线下方的交点
                    lower_left = [p for p in left_intersections if p[1] <= y_pos]
                    if lower_left:
                        lower_end = min(lower_left, key=lambda p: p[1])
                    else:
                        lower_end = (x_min, 0.0)  # 默认到底部边界

                else:  # 一般区域的处理
                    # 上半部分：左侧上方点到右侧上方点
                    upper_left = [p for p in left_intersections if p[1] >= y_pos]
                    upper_right = [p for p in right_intersections if p[1] >= y_pos]

                    if upper_left:
                        upper_start = max(upper_left, key=lambda p: p[1])
                    else:
                        upper_start = (x_min, y_pos)

                    if upper_right:
                        upper_end = max(upper_right, key=lambda p: p[1])
                    else:
                        upper_end = (x_max, y_pos)

                    # 下半部分：左侧下方点到右侧下方点
                    lower_left = [p for p in left_intersections if p[1] <= y_pos]
                    lower_right = [p for p in right_intersections if p[1] <= y_pos]

                    if lower_left:
                        lower_start = min(lower_left, key=lambda p: p[1])
                    else:
                        lower_start = (x_min, y_pos)

                    if lower_right:
                        lower_end = min(lower_right, key=lambda p: p[1])
                    else:
                        lower_end = (x_max, y_pos)

                # 添加上下区域的端点
                all_endpoints.append({
                    'region': region_num,
                    'subregion': 'upper',
                    'start': upper_start,
                    'end': upper_end
                })

                all_endpoints.append({
                    'region': region_num,
                    'subregion': 'lower',
                    'start': lower_start,
                    'end': lower_end
                })
            else:
                # 没有水平分隔线，整个区域作为一个整体
                # 选择合适的起点和终点（通常是左上到右下）
                if left_intersections and right_intersections:
                    start_point = max(left_intersections, key=lambda p: p[1])  # 左侧最上方的点
                    end_point = min(right_intersections, key=lambda p: p[1])  # 右侧最下方的点

                    all_endpoints.append({
                        'region': region_num,
                        'subregion': 'whole',
                        'start': start_point,
                        'end': end_point
                    })
                else:
                    # 处理边缘情况
                    start_point = (x_min, self.layout_manager.rows / 2)
                    end_point = (x_max, self.layout_manager.rows / 2)

                    all_endpoints.append({
                        'region': region_num,
                        'subregion': 'whole',
                        'start': start_point,
                        'end': end_point
                    })

        return all_endpoints

