# FastAPI与Playwright集成示例

本项目展示了如何使用FastAPI框架与Playwright结合，实现一个简单的Web自动化和数据抓取服务。它支持动态地创建浏览器页面（以及其中的标签页），执行简单的浏览器操作如滚动、数据选择，并允许关闭特定的标签页或页面。

## 功能特点

- **动态页面管理**：动态创建和管理浏览器页面及标签页。
- **自定义代理配置**：创建页面时支持自定义代理设置。
- **支持常见操作**：包括页面跳转、滚动到底部、选择特定数据等操作。
- **优雅的生命周期管理**：利用FastAPI的事件处理机制管理Playwright浏览器实例的生命周期。

## 快速开始

### 环境准备

确保您的系统已安装Python 3.7或更高版本。然后，安装所需的依赖：

```bash
pip install -r requirements.txt // pip install fastapi uvicorn playwright
playwright install
```

### 运行服务

克隆此仓库，然后在仓库根目录下运行：

```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

这将启动服务，并在`0.0.0.0:8000`上监听请求。

## API接口

### 创建新页面

- **请求方式**：`POST`
- **路径**：`/create_page/`
- **参数**：可选，代理服务器相关配置。
- **返回**：新创建的页面ID和初始标签页ID。

### 创建新标签页

- **请求方式**：`POST`
- **路径**：`/create_tab/{page_id}`
- **参数**：页面ID。
- **返回**：新创建的标签页ID及其URL。

### 执行页面操作

- **请求方式**：`POST`
- **路径**：`/use_page/{page_id}/{tab_id}`
- **参数**：页面ID、标签页ID、操作类型及其他可选参数。
- **返回**：根据操作类型返回相应的数据或确认信息。

### 关闭特定标签页

- **请求方式**：`DELETE`
- **路径**：`/close_tab/{page_id}/{tab_id}`
- **参数**：页面ID和标签页ID。
- **返回**：确认信息。

### 关闭页面及其所有标签页

- **请求方式**：`DELETE`
- **路径**：`/close_page/{page_id}`
- **参数**：页面ID。
- **返回**：确认信息。

### 获取所有页面及其标签页URLs

- **请求方式**：`GET`
- **路径**：`/get_pages/`
- **返回**：所有页面及其标签页的URL列表。

## 注意事项

- 请确保按照环境准备部分正确安装所有依赖项。
- 此示例默认在非无头模式下启动Chromium浏览器，可根据需要调整。
- 如果使用代理则无法使用不加代理的浏览器访问页面,创建页面时必须要加代理。

## 动作示例
~~~
example = {
        "0": {
            "action": "route",
            "url": "https://www.baidu.com",
            "timeout": 30000
        },
        "1": {
            "action": "scroll_to_bottom",
            "nums": 0,
            "height": 100
        },
        "2": {
            "action": "select_data",
            "selector": "div",
            "data": "text"
        },
        "3": {
            "action": "source",
            "data": "html"
        },
        "4": {
            "action": "pdf"
        },
        "5": {
            "action": "click_next_page",
            "selector": ".next"
        },
        "6": {
            "action": "gne_html",
            "params": {
                "title_xpath": "",
                "host": ""
                "author_xpath": "",
                "publish_time_xpath": "",
                "body_xpath": "",
                "noise_node_list": "",  // 去除节点列表xpath ['//div[@class="comment-list"]']
                "with_body_html": "False",
                "use_visible_info": "False"
            }
        },
    }
~~~

---