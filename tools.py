from bs4 import BeautifulSoup, Comment
from gne import GeneralNewsExtractor, ListPageExtractor
import re
from datetime import datetime, timedelta


class Tools:
    def __init__(self, remove_tags=None, remove_comments=False, return_html=False):
        if remove_tags is None:
            remove_tags = ["script", "style"]
        self.remove_tags = remove_tags
        self.remove_comments = remove_comments
        self.return_html = return_html

    def remove_tags(self, html_content):
        try:
            soup = BeautifulSoup(html_content, "lxml")
            if self.remove_comments:
                for comment in soup.find_all(text=lambda t: isinstance(text, Comment)):
                    comment.extract()

            for tag in soup(self.remove_tags):
                tag.decompose()
            if self.return_html:
                html = soup.prettify()
                return html
            else:
                text = soup.get_text()
                text = re.sub(r'\s+', ' ', text)
                text = re.sub(r'\u3000|\xa0', ' ', text)
                return text.strip()
        except Exception as e:
            return f"Error processing HTML content: {str(e)}"

    @staticmethod
    def extract_news_text(html,
                          title_xpath='', host='', author_xpath='',
                          publish_time_xpath='', body_xpath='', noise_node_list=None,
                          with_body_html=False, use_visible_info=False):
        if noise_node_list == "":
            noise_node_list = None
        if with_body_html == "False":
            with_body_html = False
        if use_visible_info == "False":
            use_visible_info = False
        extractor = GeneralNewsExtractor()
        result = extractor.extract(html,
                                   title_xpath=title_xpath,
                                   host=host,
                                   author_xpath=author_xpath,
                                   publish_time_xpath=publish_time_xpath,
                                   body_xpath=body_xpath,
                                   noise_node_list=noise_node_list,
                                   with_body_html=with_body_html,
                                   use_visiable_info=use_visible_info)
        return result

    @staticmethod
    def extract_list_page(html, feature):
        extractor = ListPageExtractor()
        result = extractor.extract(html, feature=feature)
        return result

    @staticmethod
    def standardize_date_zh(created_at):
        """标准化微博发布时间"""
        if "刚刚" in created_at:
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M")
        elif "秒" in created_at:
            second = created_at[:created_at.find(u"秒")]
            second = timedelta(seconds=int(second))
            created_at = (datetime.now() - second).strftime("%Y-%m-%d %H:%M")
        elif "分钟" in created_at:
            minute = created_at[:created_at.find(u"分钟")]
            minute = timedelta(minutes=int(minute))
            created_at = (datetime.now() - minute).strftime("%Y-%m-%d %H:%M")
        elif "小时" in created_at:
            hour = created_at[:created_at.find(u"小时")]
            hour = timedelta(hours=int(hour))
            created_at = (datetime.now() - hour).strftime("%Y-%m-%d %H:%M")
        elif "今天" in created_at:
            today = datetime.now().strftime('%Y-%m-%d')
            created_at = today + ' ' + created_at[2:]
        elif '年' not in created_at:
            year = datetime.now().strftime("%Y")
            month = created_at[:2]
            day = created_at[3:5]
            time = created_at[6:]
            created_at = year + '-' + month + '-' + day + ' ' + time
        else:
            year = created_at[:4]
            month = created_at[5:7]
            day = created_at[8:10]
            time = created_at[11:]
            created_at = year + '-' + month + '-' + day + ' ' + time
        return created_at

    @staticmethod
    def standardize_date_en(created_at):
        """Standardize the publication time for English social media posts."""
        if "just now" in created_at:
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M")
        elif "seconds" in created_at:
            seconds = int(created_at.split()[0])
            created_at = (datetime.now() - timedelta(seconds=seconds)).strftime("%Y-%m-%d %H:%M")
        elif "minutes" in created_at:
            minutes = int(created_at.split()[0])
            created_at = (datetime.now() - timedelta(minutes=minutes)).strftime("%Y-%m-%d %H:%M")
        elif "hours" in created_at:
            hours = int(created_at.split()[0])
            created_at = (datetime.now() - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M")
        elif "today" in created_at:
            time = created_at.split(" at ")[1]
            today = datetime.now().strftime('%Y-%m-%d')
            created_at = f'{today} {time}'
        elif "yesterday" in created_at:
            time = created_at.split(" at ")[1]
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            created_at = f'{yesterday} {time}'
        else:
            # Assumes the input is in a format like "April 15 at 14:30"
            month_day, time = created_at.split(" at ")
            year = datetime.now().year
            month = datetime.strptime(month_day.split()[0], "%B").month
            day = int(month_day.split()[1])
            created_at = datetime(year, month, day, int(time.split(":")[0]), int(time.split(":")[1])).strftime(
                "%Y-%m-%d %H:%M")
        return created_at

    @staticmethod
    def str_to_time(text):
        """将字符串转换成时间类型"""
        result = datetime.strptime(text, '%Y-%m-%d')
        return result
