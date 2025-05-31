import numpy as np


class RegionDivider:
    def __init__(self, layout_manager):
        """初始化区域划分器，接收LayoutManager作为参数"""
        self.layout_manager = layout_manager
        self.valid_grid = 1 - self.layout_manager.grid
        self.boundary_polygon = None
        self.obstacle_polygons = []
        self.grid_area = np.sum(self.valid_grid)

    def calculate_region_areas(self, divider_positions):
        """计算每个区域的面积（有效网格数）"""
        # 添加边界点，确保都是整数
        divider_positions = [int(pos) for pos in divider_positions]
        all_dividers = [0] + divider_positions + [self.layout_manager.cols]

        areas = []
        for i in range(len(all_dividers) - 1):
            x_min = all_dividers[i]
            x_max = all_dividers[i + 1]

            # 计算该区域内有效网格的数量
            area = np.sum(self.valid_grid[:, x_min:x_max])
            areas.append(area)

        return areas

    def calculate_subregion_areas(self, vertical_dividers, horizontal_dividers):
        """计算经过横线划分后每个子区域的面积"""
        all_vertical_dividers = [0] + vertical_dividers + [self.layout_manager.cols]

        # 创建一个映射，用于快速查找水平分隔线位置
        h_divider_map = {}
        for x_min, x_max, y_pos in horizontal_dividers:
            h_divider_map[(x_min, x_max)] = y_pos

        subregion_areas = []

        for i in range(len(all_vertical_dividers) - 1):
            x_min = all_vertical_dividers[i]
            x_max = all_vertical_dividers[i + 1]

            # 检查该区域是否有水平分隔线
            h_pos = None
            for hd in horizontal_dividers:
                if hd[0] == x_min and hd[1] == x_max:
                    h_pos = hd[2]
                    break

            if h_pos is not None:
                # 计算上半部分面积
                upper_area = np.sum(self.valid_grid[:h_pos, x_min:x_max])

                # 计算下半部分面积
                lower_area = np.sum(self.valid_grid[h_pos:, x_min:x_max])

                # 将结果添加到列表中
                subregion_areas.append({
                    'region': i + 1,
                    'total_area': upper_area + lower_area,
                    'upper_area': upper_area,
                    'lower_area': lower_area,
                    'horizontal_divider': h_pos
                })
            else:
                # 该区域没有水平分隔线
                total_area = np.sum(self.valid_grid[:, x_min:x_max])
                subregion_areas.append({
                    'region': i + 1,
                    'total_area': total_area,
                    'upper_area': None,
                    'lower_area': None,
                    'horizontal_divider': None
                })

        return subregion_areas

    def generate_vertical_dividers(self, num_regions=5):
        """生成垂直分隔线，均匀分割区域"""
        min_x = 0
        max_x = self.layout_manager.cols

        # 计算理想的区域宽度
        total_area = self.grid_area
        target_area_per_region = total_area / num_regions
        print(f"总面积: {total_area}, 目标每区域面积: {target_area_per_region}")

        # 初始化分隔线位置
        divider_positions = []
        cumulative_area = 0

        # 计算每列的面积
        column_areas = [np.sum(self.valid_grid[:, x]) for x in range(max_x)]

        # 从左向右扫描，按面积累计划分
        for x in range(1, max_x):
            # 累加当前列的面积
            cumulative_area += column_areas[x - 1]  # x-1 是因为列索引从0开始

            # 如果累计面积达到或超过目标面积，并且还没有分配足够的分隔线
            if cumulative_area >= target_area_per_region and len(divider_positions) < num_regions - 1:
                print(f"位置 {x} 的累计面积: {cumulative_area}")
                divider_positions.append(x)
                # 重置累计面积，开始下一个区域的面积计算
                cumulative_area = 0

        return divider_positions

    def generate_horizontal_dividers(self, vertical_dividers):
        """为每个由竖线划分的区域生成水平分隔线，使上下两部分有效面积尽量均匀"""
        all_vertical_dividers = [0] + vertical_dividers + [self.layout_manager.cols]

        horizontal_dividers = []

        # 对每个竖线划分的区域计算水平分隔线
        for i in range(len(all_vertical_dividers) - 1):
            x_min = all_vertical_dividers[i]
            x_max = all_vertical_dividers[i + 1]

            # 截取该区域的有效网格
            region_valid_grid = self.valid_grid[:, x_min:x_max]

            # 计算该区域内每行的有效网格数量
            row_valid_counts = [np.sum(region_valid_grid[row, :]) for row in range(self.layout_manager.rows)]

            # 计算该区域总的有效网格数量
            total_valid_count = np.sum(row_valid_counts)

            # 如果该区域没有有效网格，则继续下一个区域
            if total_valid_count == 0:
                continue

            # 目标是找到一个水平线，使得上下两部分有效网格数量尽量接近
            target_count = total_valid_count / 2

            # 从上到下累积计算有效网格数量
            cumulative_count = 0
            best_position = 0
            min_diff = float('inf')

            for row in range(self.layout_manager.rows):
                cumulative_count += row_valid_counts[row]

                # 计算上下两部分有效网格数量差
                count_diff = abs(cumulative_count - (total_valid_count - cumulative_count))

                # 如果找到更好的分割点
                if count_diff < min_diff:
                    min_diff = count_diff
                    best_position = row + 1  # +1 因为我们要在行之间放置分隔线

            # 保存该区域的水平分隔线位置
            horizontal_dividers.append((x_min, x_max, best_position))

        return horizontal_dividers
