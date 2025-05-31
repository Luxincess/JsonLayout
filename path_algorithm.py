import numpy as np
import time
from collections import deque


class ObstacleAwareLongestPath:
    def __init__(self, rows, cols, obstacles, start, target):
        self.rows = rows
        self.cols = cols
        self.grid = np.zeros((rows, cols), dtype=int)
        self.path = []


        # 设置障碍物
        for i, j in obstacles:
            self.grid[i, j] = 1

        # 设置起点和终点
        self.start = start
        self.target = target

        # 性能监控
        self.time_tracking = {}

        self.available_grids = np.sum(self.grid == 0)

    def calculate_coverage(self, path):
        """计算路径覆盖率"""
        total_available = np.sum(self.grid == 0)
        if not path or total_available == 0:
            return 0.0

        # 计算路径覆盖的网格数（不重复计算）
        path_cells = set()

        for cell in path:
            path_cells.add(cell)

        coverage = (len(path_cells) / total_available) * 100
        return coverage

    def is_valid_cell(self, i, j):
        """检查单元格是否有效（在网格内且不是障碍物）"""
        return 0 <= i < self.rows and 0 <= j < self.cols and self.grid[i, j] == 0

    def hamilton_path(self):
        """生成哈密顿路径，确保覆盖尽可能多的网格而不交叉"""
        print("生成哈密顿路径...")
        start_time = time.time()

        # 创建访问标记和路径记录
        visited = np.zeros((self.rows, self.cols), dtype=bool)
        path = []

        # 标记障碍物为已访问
        for i in range(self.rows):
            for j in range(self.cols):
                if self.grid[i, j] == 1:
                    visited[i, j] = True

        # 移动方向：右、下、左、上
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]

        # 预处理：标记从给定位置无法到达终点的点为已访问
        target_i, target_j = self.target

        # 使用DFS生成哈密顿路径
        def dfs(i, j):
            # 如果当前位置无效或已访问，返回False
            if not (0 <= i < self.rows and 0 <= j < self.cols) or visited[i, j]:
                return False

            # 标记当前位置为已访问
            visited[i, j] = True
            path.append((i, j))

            # 如果已经到达终点
            if (i, j) == self.target:
                return True

            # 按照蛇形模式尝试四个方向
            # 计算到终点的曼哈顿距离作为启发式，优先选择远离终点的方向
            dirs_with_heuristic = []
            for d, (di, dj) in enumerate(directions):
                ni, nj = i + di, j + dj
                if 0 <= ni < self.rows and 0 <= nj < self.cols and not visited[ni, nj]:
                    # 计算到终点的曼哈顿距离
                    dist_to_target = abs(ni - target_i) + abs(nj - target_j)
                    dirs_with_heuristic.append((d, dist_to_target))

            # 按照到终点的距离排序，优先选择更远的方向（除非已经接近终点）
            # 如果路径长度很短，我们希望接近终点；否则希望远离终点
            if len(path) < self.rows * self.cols * 0.7:  # 路径还不够长
                dirs_with_heuristic.sort(key=lambda x: -x[1])  # 优先选择远离终点的方向
            else:
                dirs_with_heuristic.sort(key=lambda x: x[1])  # 优先选择接近终点的方向

            # 尝试每个方向
            for d, _ in dirs_with_heuristic:
                di, dj = directions[d]
                ni, nj = i + di, j + dj
                if dfs(ni, nj):
                    return True

            # 如果无法继续，回溯
            path.pop()
            visited[i, j] = False
            return False

        # 从起点开始DFS
        start_i, start_j = self.start 
        success = dfs(start_i, start_j) #todo:没成功怎么处理？

        # if not success:
        #     print("警告：无法找到从起点到终点的哈密顿路径！回退到简单路径...")
        #     # 如果DFS失败，尝试简单路径
        #     path = self.meander_path()

        print(f"哈密顿路径生成完成，路径长度为 {len(path)}")
        self.time_tracking["哈密顿路径生成"] = time.time() - start_time
        return path

    def meander_path(self):
        """根据起点和终点位置生成优化的蛇形路径"""
        print("生成蛇形路径...")
        start_time = time.time()

        # 初始化路径
        path = []
        visited = np.zeros((self.rows, self.cols), dtype=bool)

        # # 标记障碍物为已访问
        # for i in range(self.rows):
        #     for j in range(self.cols):
        #         if self.grid[i, j] == 1:
        #             visited[i, j] = True

        # 添加起点
        start_i, start_j = self.start
        target_i, target_j = self.target
        path.append((start_i, start_j))
        visited[start_i, start_j] = True

        # 确定蛇形的主要方向（水平或垂直）
        # 如果起点和终点在同一侧（上下或左右），优先选择水平方向
        is_vertical_sides = (start_j == 0 and target_j == 0) or (start_j == self.cols - 1 and target_j == self.cols - 1)
        is_horizontal_sides = (start_i == 0 and target_i == 0) or (
                    start_i == self.rows - 1 and target_i == self.rows - 1)

        # 根据起点终点的位置关系选择蛇形方向
        horizontal_sweep = is_vertical_sides or (not is_horizontal_sides and self.cols > self.rows)#* 为了减少不必要的拐弯

        if horizontal_sweep:
            # 水平扫描（从上到下的蛇形 #*或从下往上）
            # 确定行的扫描顺序
            start_row = 0 if start_i <= self.rows // 2 else self.rows - 1
            row_dir = 1 if start_row == 0 else -1   #* 扫描方向

            for row_offset in range(self.rows):
                row = start_row + row_offset * row_dir
                if 0 <= row < self.rows:
                    # 确定列的扫描顺序（蛇形）
                    #* 偶数行从左往右，奇数行从右往左
                    #* 通过start_j的位置来确定每行的扫描顺序 start_j == 0 偶数行从左往右， start_j == self.cols-1 偶数行从右往左
                    col_range = range(0, self.cols) if row_offset % 2 == 0 else range(self.cols - 1, -1, -1)
                    for col in col_range:
                        if not visited[row, col]:
                            # 如果当前点与路径最后一点不相邻，需找一条连接路径
                            last_i, last_j = path[-1]   #* 取列表的最后一个元素
                            if abs(last_i - row) + abs(last_j - col) > 1: #* 不相邻
                                connecting_path = self.bfs_path((last_i, last_j), (row, col), visited) #*这样就可以不用bfs
                                if connecting_path:
                                    for p in connecting_path[1:]:
                                        path.append(p)
                                        visited[p] = True

                            path.append((row, col))
                            visited[row, col] = True
        else:
            # 垂直扫描（从左到右的蛇形）
            # 确定列的扫描顺序
            start_col = 0 if start_j <= self.cols // 2 else self.cols - 1
            col_dir = 1 if start_col == 0 else -1

            for col_offset in range(self.cols):
                col = start_col + col_offset * col_dir
                if 0 <= col < self.cols:
                    # 确定行的扫描顺序（蛇形）
                    #* 跟line164的修改思路一致
                    row_range = range(0, self.rows) if col_offset % 2 == 0 else range(self.rows - 1, -1, -1)
                    for row in row_range:
                        if not visited[row, col]:
                            # 如果当前点与路径最后一点不相邻，需找一条连接路径
                            last_i, last_j = path[-1]
                            if abs(last_i - row) + abs(last_j - col) > 1:
                                connecting_path = self.bfs_path((last_i, last_j), (row, col), visited)
                                if connecting_path:
                                    for p in connecting_path[1:]:
                                        path.append(p)
                                        visited[p] = True

                            path.append((row, col))
                            visited[row, col] = True

        # 确保终点在路径的最后
        if path[-1] != self.target:
            if self.target in path:
                # 终点已在路径中但不是最后一个点
                target_index = path.index(self.target)
                path = path[:target_index + 1]
            else:
                # 终点不在路径中，尝试找到到终点的路径
                last_point = path[-1]
                to_target = self.bfs_path(last_point, self.target, visited)
                if to_target:
                    path.extend(to_target[1:])

        self.time_tracking["蛇形路径生成"] = time.time() - start_time
        return path

    def generate_longest_path(self):
        """根据障碍物情况选择路径生成策略"""
        total_start_time = time.time()
        print("开始生成障碍物感知最长路径...")

        # 检查是否有障碍物
        has_obstacles = len(np.where(self.grid == 1)[0]) > 0

        # 选择最佳的路径生成策略
        if has_obstacles:
            print("检测到障碍物，尝试哈密顿路径...")
            path = self.hamilton_path()
        else:
            print("无障碍物，使用蛇形路径生成...")
            path = self.meander_path()

        # 验证路径有效性
        if not self.is_valid_path(path):
            print("警告：生成的路径无效（可能存在交叉）！尝试蛇形路径...")
            path = self.meander_path()

        self.path = path
        total_time = time.time() - total_start_time
        self.time_tracking["总执行时间"] = total_time

        print(f"最长路径生成完成！路径长度: {len(path)}, 总耗时: {total_time:.2f}秒")
        return path

    def bfs_path(self, start, target, visited):
        """使用BFS找到从起点到终点的最短路径"""
        queue = deque([(start[0], start[1], [])])
        temp_visited = visited.copy()
        temp_visited[start] = True

        # 移动方向：右、下、左、上
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]

        while queue:
            i, j, current_path = queue.popleft()
            current_path = current_path + [(i, j)]

            if (i, j) == target:
                return current_path

            for di, dj in directions:
                ni, nj = i + di, j + dj
                if 0 <= ni < self.rows and 0 <= nj < self.cols and not temp_visited[ni, nj]:
                    temp_visited[ni, nj] = True
                    queue.append((ni, nj, current_path))

        return []  # 无法找到路径

    def is_valid_path(self, path):
        """检查路径是否有效（无交叉）"""
        # 检查每个点是否只出现一次
        points_set = set()
        for point in path:
            if point in points_set:
                return False
            points_set.add(point)

        # 检查相邻点是否真的相邻
        for i in range(1, len(path)):
            prev = path[i - 1]
            curr = path[i]
            if abs(prev[0] - curr[0]) + abs(prev[1] - curr[1]) != 1:
                return False

        return True



