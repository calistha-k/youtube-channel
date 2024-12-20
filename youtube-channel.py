from tkinter import *
from tkinter.font import *
from PIL import ImageTk, Image
from io import BytesIO
import urllib.parse  # 用於處理中文編碼
import urllib.request as request
import json
import webbrowser

# API 金鑰
API_KEY = "AIzaSyBAYG7ThWLOc9tvNZUEVuiDe5-GEAUnE08"  # 請替換成有效的 API 金鑰

def fetch_channel_suggestions(event):
    name = Channel.get().strip()  # 取得使用者輸入並去除多餘空格
    if not name:
        suggestion_listbox.delete(0, END)
        return

    # 中文名稱進行 URL 編碼
    encoded_name = urllib.parse.quote(name)
    search_url = f'https://youtube.googleapis.com/youtube/v3/search?part=snippet&type=channel&q={encoded_name}&key={API_KEY}'

    try:
        # 搜索頻道
        with request.urlopen(search_url) as response:
            search_data = json.load(response)
        
        suggestion_listbox.delete(0, END)  # 清空原有建議

        if "items" in search_data and search_data["items"]:
            for item in search_data["items"]:
                channel_name = item["snippet"]["title"]
                suggestion_listbox.insert(END, channel_name)  # 顯示建議

    except Exception as e:
        print(f"Error fetching suggestions: {e}")

def select_suggestion(event):
    # 取得選擇的頻道名稱
    selected_channel = suggestion_listbox.get(suggestion_listbox.curselection())
    Channel.delete(0, END)
    Channel.insert(0, selected_channel)
    suggestion_listbox.delete(0, END)  # 清空建議列表
    fetch_channel_info()  # 搜索頻道資訊

def fetch_channel_info():
    name = Channel.get().strip()  # 取得使用者輸入並去除多餘空格
    if not name:
        error_label.config(text="請輸入頻道名稱！", fg="red")
        return

    # 中文名稱進行 URL 編碼
    encoded_name = urllib.parse.quote(name)
    search_url = f'https://youtube.googleapis.com/youtube/v3/search?part=snippet&type=channel&q={encoded_name}&key={API_KEY}'
    
    try:
        # 搜索頻道
        with request.urlopen(search_url) as response:
            search_data = json.load(response)
        
        if "items" not in search_data or not search_data["items"]:
            raise ValueError("找不到該頻道，請確認名稱是否正確！")
        
        # 取得頻道 ID
        channel_id = search_data["items"][0]["id"]["channelId"]
        fetch_detailed_info(channel_id)
    except Exception as e:
        error_label.config(text=f"Error: {e}", fg="red")

def fetch_detailed_info(channel_id):
    channel_url = f'https://youtube.googleapis.com/youtube/v3/channels?part=snippet,statistics,topicDetails&id={channel_id}&key={API_KEY}'
    videos_url = f'https://youtube.googleapis.com/youtube/v3/search?part=snippet&channelId={channel_id}&order=date&maxResults=1&type=video&key={API_KEY}'
    try:
        # 獲取頻道資訊
        with request.urlopen(channel_url) as response:
            channel_data = json.load(response)
        
        if "items" not in channel_data or not channel_data["items"]:
            raise ValueError("找不到該頻道資訊！")
        
        # 更新頻道基本資訊
        channel_name.config(text=channel_data["items"][0]["snippet"]["title"])
        channel_view2.config(text=f'{int(channel_data["items"][0]["statistics"]["viewCount"]):,}')
        channel_video2.config(text=channel_data["items"][0]["statistics"]["videoCount"])
        channel_subscribe2.config(text=channel_data["items"][0]["statistics"].get("subscriberCount", "隱藏"))
        
        # 頻道主題
        topics = channel_data["items"][0].get("topicDetails", {}).get("topicCategories", [])
        topic_text = " | ".join([topic.split('/')[-1].replace('_', ' ') for topic in topics]) if topics else "無"
        channel_topic.config(text=topic_text)

        # 頻道縮圖
        url = channel_data["items"][0]["snippet"]["thumbnails"]["default"]['url']
        image_bytes = request.urlopen(url).read()
        data_stream = BytesIO(image_bytes)
        pil_image = Image.open(data_stream)
        global tk_image  # 避免圖片被垃圾回收
        tk_image = ImageTk.PhotoImage(pil_image)
        channel_pic.config(image=tk_image)

        error_label.config(text="")

        # 獲取最新影片
        with request.urlopen(videos_url) as response:
            video_data = json.load(response)
        
        if "items" in video_data and video_data["items"]:
            video_id = video_data["items"][0]["id"]["videoId"]
            video_title = video_data["items"][0]["snippet"]["title"]
            video_thumb_url = video_data["items"][0]["snippet"]["thumbnails"]["default"]["url"]

            # 更新最新影片資訊
            latest_video_title.config(text=video_title)
            latest_video_btn.config(command=lambda: open_video(video_id))
            
            # 最新影片縮圖
            video_image_bytes = request.urlopen(video_thumb_url).read()
            video_data_stream = BytesIO(video_image_bytes)
            video_pil_image = Image.open(video_data_stream)
            global tk_video_image
            tk_video_image = ImageTk.PhotoImage(video_pil_image)
            latest_video_thumb.config(image=tk_video_image)
        else:
            latest_video_title.config(text="無最新影片資訊")
    except Exception as e:
        error_label.config(text=f"Error: {e}", fg="red")

def open_video(video_id):
    webbrowser.open(f'https://www.youtube.com/watch?v={video_id}')

# GUI 設定
window = Tk()
window.title('YouTube Channel Info')
window.geometry('800x650')
window.config(bg="#323232")

# 輸入框
Channel = Entry(window, width=40)
Channel.place(anchor=CENTER, x=400, y=20)

# 監聽輸入框事件以顯示建議
Channel.bind("<KeyRelease>", fetch_channel_suggestions)

# 建議清單框
suggestion_listbox = Listbox(window, width=40, height=6, bg="#323232", fg="White", font=Font(size=12))
suggestion_listbox.place(x=400, y=50)
suggestion_listbox.bind("<Double-1>", select_suggestion)

# 確認按鈕
done = Button(window, text="查詢", command=fetch_channel_info)
done.config(height=1, width=10)
done.place(anchor=CENTER, x=400, y=200)

# 頻道名稱
channel_name = Label(window, text="", bg="#323232", fg="White", font=Font(size=25))
channel_name.place(anchor=CENTER, x=400, y=250)

# 頻道縮圖
channel_pic = Label(window, bg="#323232")
channel_pic.place(x=50, y=220)

# 頻道瀏覽次數
channel_view = Label(window, text="觀看次數", bg="#323232", fg="White", font=Font(size=15))
channel_view.place(anchor=CENTER, x=200, y=350)
channel_view2 = Label(window, text="", bg="#323232", fg="White", font=Font(size=13))
channel_view2.place(anchor=CENTER, x=200, y=380)

# 頻道影片總數
channel_video = Label(window, text="影片總數", bg="#323232", fg="White", font=Font(size=15))
channel_video.place(anchor=CENTER, x=400, y=350)
channel_video2 = Label(window, text="", bg="#323232", fg="White", font=Font(size=13))
channel_video2.place(anchor=CENTER, x=400, y=380)

# 頻道訂閱數
channel_subscribe = Label(window, text="訂閱數", bg="#323232", fg="White", font=Font(size=15))
channel_subscribe.place(anchor=CENTER, x=600, y=350)
channel_subscribe2 = Label(window, text="", bg="#323232", fg="White", font=Font(size=13))
channel_subscribe2.place(anchor=CENTER, x=600, y=380)

# 頻道主題
channel_topic_label = Label(window, text="頻道主題", bg="#323232", fg="White", font=Font(size=15))
channel_topic_label.place(anchor=CENTER, x=400, y=450)
channel_topic = Label(window, text="", bg="#323232", fg="White", font=Font(size=13))
channel_topic.place(anchor=CENTER, x=400, y=480)

# 最新影片
latest_video_label = Label(window, text="最新影片", bg="#323232", fg="White", font=Font(size=15))
latest_video_label.place(anchor=CENTER, x=400, y=530)
latest_video_title = Label(window, text="", bg="#323232", fg="White", font=Font(size=13))
latest_video_title.place(anchor=CENTER, x=400, y=560)

latest_video_btn = Button(window, text="播放影片", command=None, bg="#555555", fg="White", font=Font(size=10))
latest_video_btn.place(anchor=CENTER, x=400, y=590)

latest_video_thumb = Label(window, bg="#323232")
latest_video_thumb.place(x=650, y=530)

# 錯誤訊息
error_label = Label(window, text="", bg="#323232", fg="White", font=Font(size=13))
error_label.place(anchor=CENTER, x=400, y=620)

window.mainloop()
