from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
from add_script import context_add_init_script
from tools import Tools
import uvicorn

app = FastAPI()
tools = Tools()
playwright = None
browser = None
pages = {}
BASE_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
           "Chrome/123.0.0.0 Safari/537.36")


class LifespanHandler:
    @staticmethod
    async def on_startup():
        global playwright, browser
        playwright = await async_playwright().start()
        # browser = await playwright.chromium.launch(headless=False)
        # 如果使用代理的话,就没法在不使用代理的情况下创建浏览器了
        browser = await playwright.chromium.launch(headless=True, proxy={"server": "http://per-context"})

    @staticmethod
    async def on_shutdown():
        await browser.close()
        await playwright.stop()


handler = LifespanHandler()
app.add_event_handler("startup", handler.on_startup)
app.add_event_handler("shutdown", handler.on_shutdown)


@app.post("/create_page/")
async def create_new_page(proxy_server: str = "", proxy_username: str = "", proxy_password: str = ""):
    proxy_config = {}
    if proxy_server:
        proxy_config['server'] = proxy_server
        if proxy_username and proxy_password:
            proxy_config['username'] = proxy_username
            proxy_config['password'] = proxy_password
    context_options = {}
    if proxy_config:
        context_options['proxy'] = proxy_config
    context_options['user_agent'] = BASE_UA
    context_options['width'] = 1920
    context_options['height'] = 1080
    context_options['languages'] = ['en-US', 'en']
    context = await context_add_init_script(browser, context_options)
    page = await context.new_page()
    await stealth_async(page)
    page_id = len(pages)
    pages[page_id] = [page]
    return {"page_id": page_id, "tab_id": 0, "url": page.url}


@app.post("/create_tab/{page_id}")
async def create_new_tab(page_id: int):
    if page_id not in pages:
        return Response(content={"message": "Page not found"}, status_code=404)
    context = pages[page_id][0].context
    new_page = await context.new_page()
    tab_id = len(pages[page_id])
    pages[page_id].append(new_page)
    return {"page_id": page_id, "tab_id": tab_id, "url": new_page.url}


@app.post("/use_page/{page_id}/{tab_id}")
async def use_page(actions: dict, page_id: int, tab_id: int):
    if page_id not in pages or tab_id >= len(pages[page_id]):
        return Response(content={"message": "Page or tab not found"}, status_code=404)
    page = pages[page_id][tab_id]
    if actions["0"]['action'] != "route":
        return Response(content={"message": "First action must be route"}, status_code=400)
    return_data = {
        "data": ""
    }
    for item in actions.keys():
        action = actions[item]
        if action["action"] == "route":
            await page.goto(action["url"], timeout=action.get("timeout", 30000))
        elif action["action"] == "scroll_to_bottom":
            await page.evaluate("""
                async ({nums, height}) => {
                    await new Promise((resolve, reject) => {
                        var totalHeight = 0;
                        var num = 0;
                        var distance = height;
                        var numss = nums;
                        var timer = setInterval(() => {
                            var scrollHeight = document.body.scrollHeight;
                            window.scrollBy(0, distance);
                            totalHeight += distance;
                            if(totalHeight >= scrollHeight){
                                clearInterval(timer);
                                resolve("ok");
                            }
                            if(num > numss*2){
                                clearInterval(timer);
                                resolve("ok");
                            }else{
                                num = num + 1;
                            }
                        }, 1000);
                    });
                }
                """, {"nums": action["nums"], "height": action["height"]})
        elif action["action"] == "select_data":
            elements = await page.query_selector_all(action["selector"])
            data = [await element.text_content() for element in elements]
            return_data['data'] = data
        elif action["action"] == "source":
            if action['data'] == "html":
                data = await page.content()
            elif action['data'] == "text":
                data = await page.text()
            else:
                data = await page.content()
            return_data['data'] = data
        elif action["action"] == "pdf":
            page_pdf = await page.pdf()
            return Response(content=page_pdf, media_type="application/pdf")
        elif action["action"] == "click_next_page":
            await page.click(action["selector"])
        elif action["action"] == "gne_html":
            if action.get("html"):
                html = action["html"]
            else:
                html = await page.content()
            data = tools.extract_news_text(html, **action["params"])
            return_data['data'] = data
            return_data['message'] = ("gne maybe not work well, please check the result."
                                      "pls add noise_node_list if needed to remove noise nodes,"
                                      "or add xpath selector for author_xpath, body_xpath ...")
        elif action["action"] == "gne_list":
            if action.get("html"):
                html = action["html"]
            else:
                html = await page.content()
            data = tools.extract_list_page(html, action["feature"])
            return_data['data'] = data
            return_data['message'] = "gne maybe not work well, please check the result"
        elif action["action"] == "remove_tags":
            if action.get("html"):
                html = action["html"]
            else:
                html = await page.content()
            data = tools.remove_tags(html)
            return_data['data'] = data
        else:
            return_data['message'] = "Action not found"
    return JSONResponse(content=return_data)


@app.delete("/close_tab/{page_id}/{tab_id}")
async def close_specific_tab(page_id: int, tab_id: int):
    if page_id not in pages or tab_id < 0 or tab_id >= len(pages[page_id]):
        return Response(content={"message": "Page or tab not found"}, status_code=404)
    await pages[page_id][tab_id].close()
    pages[page_id].pop(tab_id)
    if not pages[page_id]:
        pages.pop(page_id)

    return {"message": "Tab closed"}


@app.delete("/close_page/{page_id}")
async def close_page(page_id: int):
    if page_id not in pages:
        return Response(content={"message": "Page not found"}, status_code=404)
    for tab in pages[page_id]:
        await tab.close()
    pages.pop(page_id)
    return {"message": "Page and all its tabs closed"}


@app.delete("/close_all_pages/")
async def close_all_pages():
    for page_id, tabs in pages.items():
        for tab in tabs:
            await tab.close()
    pages.clear()
    return {"message": "All pages and tabs closed"}


@app.get("/get_pages/")
async def get_pages():
    pages_info = {}
    for page_id, tabs in pages.items():
        pages_info[page_id] = [tab.url for tab in tabs]
    return pages_info


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
