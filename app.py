from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
import uvicorn

app = FastAPI()
playwright = None
browser = None
pages = {}  # 使用字典存储页面ID及其下的标签页列表


class LifespanHandler:
    async def on_startup(self):
        global playwright, browser
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=False)

    async def on_shutdown(self):
        await browser.close()
        await playwright.stop()


handler = LifespanHandler()
app.add_event_handler("startup", handler.on_startup)
app.add_event_handler("shutdown", handler.on_shutdown)


@app.post("/create_page/")
async def create_new_page():
    context = await browser.new_context()
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
async def use_page(page_id: int, tab_id: int, action: str, url: str = "", selector: str = "", nums: int = 0, height: int = 100):
    if page_id not in pages or tab_id >= len(pages[page_id]):
        raise HTTPException(status_code=404, detail="Tab not found")
    page = pages[page_id][tab_id]
    await page.goto(url)
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
    else:
        raise HTTPException(status_code=400, detail="Invalid action")


@app.delete("/close_tab/{page_id}/{tab_id}")
async def close_tab(page_id: int, tab_id: int):
    if page_id not in pages or tab_id >= len(pages[page_id]):
        raise HTTPException(status_code=404, detail="Tab not found")
    await pages[page_id][tab_id].close()
    pages[page_id].pop(tab_id)
    if not pages[page_id]:
        pages.pop(page_id)
    return {"message": "Tab closed"}


@app.get("/get_pages/")
async def get_pages():
    pages_info = {}
    for page_id, tabs in pages.items():
        pages_info[page_id] = [tab.url for tab in tabs]
    return pages_info


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
