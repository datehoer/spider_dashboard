from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import JSONResponse
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
from add_script import context_add_init_script
import uvicorn

app = FastAPI()
playwright = None
browser = None
pages = {}


class LifespanHandler:
    async def on_startup(self):
        global playwright, browser
        playwright = await async_playwright().start()
        # browser = await playwright.chromium.launch(headless=False)
        # 如果使用代理的话,就没法在不使用代理的情况下创建浏览器了
        browser = await playwright.chromium.launch(headless=True, proxy={"server": "http://per-context"})

    async def on_shutdown(self):
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
    context_options['user_agent'] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
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
        raise HTTPException(status_code=404, detail="Page not found")
    context = pages[page_id][0].context
    new_page = await context.new_page()
    tab_id = len(pages[page_id])
    pages[page_id].append(new_page)
    return {"page_id": page_id, "tab_id": tab_id, "url": new_page.url}


@app.post("/use_page/{page_id}/{tab_id}")
async def use_page(page_id, tab_id, action, url: str = "", selector: str = "", nums=0, height=100, timeout=30000):
    example = {
        "0": {
            "action": "route",
            "url": "https://www.baidu.com"
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
        },
        "4": {
            "action": "pdf"
        },
        "5": {
            "action": "click_next_page",
            "selector": ".next"
        }

    }
    if page_id not in pages or tab_id >= len(pages[page_id]):
        raise HTTPException(status_code=404, detail="Tab not found")
    page = pages[page_id][tab_id]
    await page.goto(url, timeout=timeout)
    actions = ["scroll_to_bottom", "select_data", "screenshot", "pdf", 'route']
    if action == "scroll_to_bottom":
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
            """, {"nums": nums, "height": height})
        return JSONResponse(content=await page.content())
    elif action == "select_data":
        elements = await page.query_selector_all(selector)
        return JSONResponse(content=[await element.text_content() for element in elements])
    elif action == "screenshot":
        return Response(content=await page.screenshot(), media_type="image/png")
    elif action == "pdf":
        return Response(content=await page.pdf(), media_type="application/pdf")
    else:
        raise HTTPException(status_code=400, detail="Invalid action")


@app.delete("/close_tab/{page_id}/{tab_id}")
async def close_specific_tab(page_id: int, tab_id: int):
    if page_id not in pages or tab_id < 0 or tab_id >= len(pages[page_id]):
        raise HTTPException(status_code=404, detail="Page or tab not found")

    await pages[page_id][tab_id].close()
    pages[page_id].pop(tab_id)

    if not pages[page_id]:
        pages.pop(page_id)

    return {"message": "Tab closed"}


@app.delete("/close_page/{page_id}")
async def close_page(page_id: int):
    if page_id not in pages:
        raise HTTPException(status_code=404, detail="Page not found")

    for tab in pages[page_id]:
        await tab.close()
    pages.pop(page_id)

    return {"message": "Page and all its tabs closed"}


@app.get("/get_pages/")
async def get_pages():
    pages_info = {}
    for page_id, tabs in pages.items():
        pages_info[page_id] = [tab.url for tab in tabs]
    return pages_info


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
