# MySQL 学习教程（Docker 环境版）

> 面向：已有 FastAPI + SQLite 基础，想补 MySQL 语法的同学。
> 数据沿用笔试常用员工表结构与字段，方便对照面试题。
> 学完可 `docker rm` 删掉容器，不污染本机。

***

## 0. 为什么用 Docker 跑 MySQL

你本机没装 MySQL，但装了 Docker Desktop。用容器跑 MySQL 的好处：

- **不污染本机**：MySQL 是个系统服务，装本地要占资源、还要配开机启动，
  容器跑在 Docker 里，不进系统服务。

- **一条命令启动 / 一条命令删除**：随时重建，学坏了大不了删掉重来。

- 前提：先打开 Docker Desktop，等左下角变成绿色 **Engine running**。

***

## 1. 启动容器（一次性）

```bash
docker run -d \
  --name mysql-learn \
  -e MYSQL_ROOT_PASSWORD=learn123 \
  -e MYSQL_DATABASE=company \
  -p 3306:3306 \
  -v mysql_data:/var/lib/mysql \
  mysql:8.0
```

拆开看每段：

| 参数                                | 含义                            |
| --------------------------------- | ----------------------------- |
| `-d`                              | 后台运行（detach），不占终端             |
| `--name mysql-learn`              | 给容器起名，后面用这个名字管理               |
| `-e MYSQL_ROOT_PASSWORD=learn123` | 设置 root 密码（学习用随便，线上绝不可用弱密码）   |
| `-e MYSQL_DATABASE=company`       | 首次启动自动创建一个叫 `company` 的库      |
| `-p 3306:3306`                    | 把容器内部 3306 端口映射到本机 3306，外部才能连 |
| `-v mysql_data:/var/lib/mysql`    | 数据落盘到 Docker 卷，删容器后数据也不丢      |
| `mysql:8.0`                       | 官方 MySQL 8.0 镜像               |

查看是否成功：

```bash
docker ps            # 看到 mysql-learn 且 STATUS 为 Up 即成功
```

***

## 2. 连接 MySQL

有两种方式。推荐方式一。

### 方式一：直接进容器里用 mysql 客户端

```bash
docker exec -it mysql-learn mysql -uroot -p
# 输入密码 learn123
```

进入后提示符变成 `mysql>`，下面所有 SQL 都在这里敲。

### 方式二：从本机连（如果装了 mysql 客户端或图形工具）

DB Browser 不支持连 MySQL，建议先只用方式一，壳是黑的但学习够了。
想用图形界面的话，装 **DBeaver**（连 MySQL、选公司库即可）。

进去后先看看自动建好的库：

```sql
SHOW DATABASES;        -- 应该看到 company
USE company;           -- 切到 company 库
```

***

## 3. 建表 + 插数据（今天的两张表）

在 `mysql>` 里粘贴执行：

```sql
-- 部门表
CREATE TABLE departments (
  id INT PRIMARY KEY AUTO_INCREMENT,
  dept_name VARCHAR(50) NOT NULL
);

-- 员工表
CREATE TABLE employees (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(50) NOT NULL,
  dept_id INT,
  salary INT
);

-- 插入部门
INSERT INTO departments (dept_name) VALUES
  ('研发部'), ('市场部'), ('财务部');

-- 插入员工（最后一名 dept_id 故意为空，用来练 LEFT JOIN）
INSERT INTO employees (name, dept_id, salary) VALUES
  ('张三', 1, 8000),
  ('李四', 1, 9500),
  ('王五', 2, 6500),
  ('赵六', 3, 9000),
  ('孙七', 2, 7200),
  ('钱八', NULL, 5000);
```

查看数据：

```sql
SELECT * FROM employees;
SELECT * FROM departments;
```

> `AUTO_INCREMENT` = 自增主键（MySQL 写法，SQLite 是 `AUTOINCREMENT`，注意差异）。

***

## 4. 基础查询

```sql
SELECT name, salary FROM employees;                  -- 查指定列
SELECT DISTINCT dept_id FROM employees;               -- 去重
SELECT * FROM employees WHERE salary > 7000;          -- 条件过滤
SELECT * FROM employees WHERE name LIKE '%张%';        -- 模糊匹配
SELECT * FROM employees ORDER BY salary DESC;         -- 排序（DESC 降序）
SELECT * FROM employees LIMIT 3;                      -- 只取前 3 行
```

> **`WHERE`** **vs** **`HAVING`**：`WHERE` 在分组前过滤普通列；`HAVING` 在分组后过滤聚合结果。

***

## 5. 聚合与分组

```sql
SELECT COUNT(*) FROM employees;               -- 共有 6 个员工
SELECT AVG(salary) FROM employees;            -- 平均工资
SELECT SUM(salary) FROM employees;            -- 工资总和
SELECT MAX(salary), MIN(salary) FROM employees;

-- 每个部门平均工资（注意钱八 dept_id 是 NULL，会被分组忽略）
SELECT dept_id, AVG(salary)
FROM employees
GROUP BY dept_id;

-- 分组后只保留平均工资 >7500 的部门
SELECT dept_id, AVG(salary) AS avg_sal
FROM employees
GROUP BY dept_id
HAVING avg_sal > 7500;
```

> **`COUNT(*)`** **vs** **`COUNT(列)`**：前者统计含 NULL 的所有行；后者只统计该列非 NULL 的行。

***

## 6. 多表 JOIN（重点）

```sql
-- INNER JOIN：两边都有才出现（钱八没部门 → 不出现）
SELECT e.name, d.dept_name
FROM employees e
INNER JOIN departments d ON e.dept_id = d.id;

-- LEFT JOIN：左表全保留，右表没有就补 NULL（钱八会显示，部门为 NULL）
SELECT e.name, d.dept_name
FROM employees e
LEFT JOIN departments d ON e.dept_id = d.id;
```

**面试经典题：查"没有部门的员工"**

```sql
SELECT e.name
FROM employees e
LEFT JOIN departments d ON e.dept_id = d.id
WHERE d.id IS NULL;          -- 结果应是：钱八
```

**面试经典题：查"每个部门工资最高的员工"**

```sql
SELECT e.dept_id, e.name, e.salary
FROM employees e
INNER JOIN (
    SELECT dept_id, MAX(salary) AS max_sal
    FROM employees
    WHERE dept_id IS NOT NULL
    GROUP BY dept_id
) m ON e.dept_id = m.dept_id AND e.salary = m.max_sal;
```

***

## 7. 窗口函数 + 子查询（加分项）

```sql
-- 窗口函数：按工资排名
SELECT name, salary,
  ROW_NUMBER() OVER (ORDER BY salary DESC) AS 排名,
  RANK()       OVER (ORDER BY salary DESC) AS 排名可并列,
  DENSE_RANK() OVER (ORDER BY salary DESC) AS 排名连续
FROM employees;

-- 子查询：工资高于全体平均水平
SELECT name, salary FROM employees
WHERE salary > (SELECT AVG(salary) FROM employees);
```

**面试高频题：每个部门工资前 3 名**

```sql
SELECT dept_id, name, salary
FROM (
  SELECT dept_id, name, salary,
    ROW_NUMBER() OVER (PARTITION BY dept_id ORDER BY salary DESC) AS rn
  FROM employees
  WHERE dept_id IS NOT NULL
) ranked
WHERE rn <= 3;
```

***

## 8. 练习后验证自己

在这套数据上，自己先写、再对照：

1. 每个部门有多少人？（`GROUP BY` + `COUNT(*)`）
2. 没分部门的员工有谁？（`LEFT JOIN` + `IS NULL`）
3. 工资高于各自部门平均值的有谁？（关联子查询或窗口函数）
4. 按工资从高到低给全员排名？（`ROW_NUMBER` + `ORDER BY`）

答案在第 10 节。

***

## 9. 常用 DDL 与管理

```sql
ALTER TABLE employees ADD COLUMN email VARCHAR(100);   -- 加列
UPDATE employees SET salary = 9800 WHERE name='张三';   -- 改数据
DELETE FROM employees WHERE name='钱八';                -- 删行
DROP TABLE employees;                                  -- 删表（危险！）
```

```bash
docker exec -it mysql-learn mysql -uroot -p   # 重新进入
docker stop mysql-learn                        # 停止容器（不删）
docker start mysql-learn                       # 重启容器
docker rm -f mysql-learn                       # 永久删除容器（数据在卷里还在）
docker volume rm mysql_data                    # 连数据卷一起删
```

***

## 10. 练习答案与参考答案对照

**Q1 每部门人数**

```sql
SELECT dept_id, COUNT(*) AS cnt
FROM employees
GROUP BY dept_id;
```

**Q2 没分部门的员工**

```sql
SELECT e.name
FROM employees e
LEFT JOIN departments d ON e.dept_id = d.id
WHERE d.id IS NULL;
```

**Q3 工资高于部门平均**

```sql
SELECT e.name, e.salary
FROM employees e
WHERE e.salary > (
  SELECT AVG(salary)
  FROM employees
  WHERE dept_id = e.dept_id
);
```

**Q4 全员排名**

```sql
SELECT name, salary,
  ROW_NUMBER() OVER (ORDER BY salary DESC) AS rn
FROM employees;
```

***

## 附：MySQL 与 SQLite 的 3 个关键差异（你说已有 SQLite 基础）

| 操作    | MySQL                | SQLite                              |
| ----- | -------------------- | ----------------------------------- |
| 自增主键  | `INT AUTO_INCREMENT` | `INTEGER PRIMARY KEY AUTOINCREMENT` |
| 大小写   | 表/库名在 Linux 下区分大小写   | 不区分                                 |
| 端口/连接 | 走 3306 端口 + 密码（服务式）  | 就是本地文件，直接打开                         |

> 你已会的 SQL 语法（SELECT/WHERE/JOIN/GROUP BY）**两边通用**，改环境主要差在这三点。

