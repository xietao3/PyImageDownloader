#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os
import os.path
import re
import urllib2
from Tkinter import *
import tkFileDialog
import threading


# 图片类
class Picture(object):

    def __init__(self, name, url, dir_path, index):
        # 该图片顺序下标  用于设置默认图片名字
        self.index = index
        # 图片名
        self.name = name
        # 图片链接
        self.url = url
        # 图片保存路径
        self.dir_path = dir_path
        # 图片下载失败原因
        self.error_reason = None

    # 开始下载
    def start_download_pic(self, download_pic_callback):
        pic_path = self.build_pic_name()

        # 已存在则不重复下载
        if os.path.exists(pic_path):
            print ('pic has existed:' + self.url)
            self.error_reason = "pic has existed:"
            download_pic_callback(self)
            return

        # 图片链接前缀不包含http
        if not self.url.startswith("http"):
            print ('pic has invalid url:' + self.url)
            self.error_reason = "pic has invalid url"
            download_pic_callback(self)
            return

        header = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.114 Safari/537.36',
            'Cookie': 'AspxAutoDetectCookieSupport=1',
        }

        # 下载图片
        request = urllib2.Request(self.url, None, header)
        try:
            response = urllib2.urlopen(request, timeout=10)
        # 下载失败
        except Exception, error:
            print ('pic cannot download:' + self.url)
            self.error_reason = str(error)
            download_pic_callback(self)
            return

        # 保存图片
        try:
            fp = open(pic_path, 'wb')
            fp.write(response.read())
            fp.close()
        # 保存失败
        except IOError, error:
            print(error)
            self.error_reason = str(error)
            download_pic_callback(self)
            return

        # 下载完成回调
        download_pic_callback(self)

    # 组装图片名字
    def build_pic_name(self):
        # 剪去图片链接后的参数
        pic_url = self.url.split("?")[0]

        # 获取图片格式后缀 如果没有 默认jpg
        urls = pic_url.split(".")
        if len(urls) > 1:
            pic_type = urls[len(urls)-1]
        else:
            pic_type = "jpg"

        # 组装图片命名
        if self.name is not None and len(self.name) > 0:
            pic_name = self.name + "." + pic_type
        else:
            pic_name = "no_name_" + str(self.index) + "." + pic_type

        pic_path = os.path.join(self.dir_path, pic_name)
        return pic_path


# 文章类
class Article(object):

    def __init__(self, path):
        # 文章的绝对路径
        self.article_path = path
        # 拼接文章图片下载后保存的路径
        self.article_pic_dir = path.replace(".md", "_Image")
        # 新建保存文章图片的文件夹
        self.mkdir_image_dir()
        # 开始搜索图片
        self.pic_list = self.find_pics(self.article_path)

    # 查找图片
    def find_pics(self, article_path):
        # 打开md文件
        f = open(article_path, 'r')
        content = f.read()
        pics = []

        # 匹配正则 match ![]()
        results = re.findall(r"!\[(.+?)\)", content)

        index = 0
        for result in results:
            temp_pic = result.split("](")
            # 将图片加入到图片数组当中
            if len(temp_pic) == 2:
                pic = Picture(temp_pic[0], temp_pic[1], self.article_pic_dir, index)
                pics.append(pic)
            index += 1
        f.close()
        return pics

    # 新建图片的保存文件夹
    def mkdir_image_dir(self):
        # 如果该文件夹不存在 则新建一个
        if not os.path.exists(self.article_pic_dir):
            os.mkdir(self.article_pic_dir)


class Directory(object):

    @classmethod
    def find_sub_path(cls, path):
        # 初始化一个空的文章列表
        article_list = []
        # 获取该文件夹下的所以子文件
        temp_files = os.listdir(path)
        # 遍历子文件
        for temp_file in temp_files:
            # 拼接该文件绝对路径
            full_path = os.path.join(path, temp_file)

            # 匹配.md文件
            if os.path.isfile(full_path) and os.path.splitext(full_path)[1] == ".md":
                # 如果是.md文件 加入文章列表
                article = Article(full_path)
                article_list.append(article)
            # 如果是文件夹 进行递归继续搜索
            elif os.path.isdir(full_path):
                # 将子文件夹中的文章列表拼接到上级目录的文章列表中
                article_list.extend(cls.find_sub_path(full_path))

        return article_list


class XTImageDownloader(object):

    def __init__(self):
        # 数据
        self.download_error_list = []
        self.all_pic_count = 0
        self.current_pic_index = 0
        self.thread_lock = threading.Lock()
        self.search_button = None
        # 图形界面相关
        self.root = Tk()
        self.root.title("XTImageDownloader")
        self.path = StringVar()
        self.title = StringVar()
        self.title.set("请选择Markdown文件所在文件夹")
        self.list_box = None
        Label(self.root, textvariable=self.title).grid(row=0, column=1)
        Label(self.root, text="文件夹路径:").grid(row=1, column=0)
        Entry(self.root, textvariable=self.path).grid(row=1, column=1)
        Button(self.root, text="选择路径", command=self.select_path).grid(row=1, column=2)
        self.root.mainloop()

    # 选择文件夹
    def select_path(self):
        self.path.set(tkFileDialog.askdirectory())
        # 用户选中文件夹之后 显示下载按钮
        if self.path.get() != "":
            self.search_button = Button(self.root, text="开始搜索并下载", command=self.start_search_dir)
            self.search_button.grid(row=2, column=1)
            return self.path

    # 开始搜索文件夹 并且下载
    def start_search_dir(self):
        self.search_button['state'] = DISABLED
        self.search_button['text'] = "正在下载..."
        
        self.all_pic_count = 0
        self.current_pic_index = 0
        self.download_error_list = []
        # 获取Markdown文件列表
        article_list = Directory.find_sub_path(self.path.get())

        # 更新搜索进度 刷新UI
        for article in article_list:
            self.all_pic_count += len(article.pic_list)
        self.change_title(self.all_pic_count, self.current_pic_index)

        # 开始下载图片
        for article in article_list:
            for pic in article.pic_list:
                # 开启异步线程下载图片 并且传入下载完成的回调
                thread = threading.Thread(target=pic.start_download_pic, args=(self.download_pic_callback,))
                thread.start()

    # 下载图片完成后的回调函数
    def download_pic_callback(self, pic):
        # 获取线程锁
        self.thread_lock.acquire()
        # 如果下载失败 则保存到失败列表
        if pic.error_reason is not None and len(pic.error_reason) > 0:
            self.download_error_list.append(pic)

        self.current_pic_index += 1

        # 更新下载进度 刷新UI
        print('finish:' + str(self.current_pic_index) + '/' + str(self.all_pic_count))
        self.change_title(self.all_pic_count, self.current_pic_index)

        # 全部下载成功 刷新UI 生成失败报告
        if self.all_pic_count == self.current_pic_index:
            self.search_button['text'] = "下载完成"
            self.print_error(self.download_error_list)

        # 释放锁
        self.thread_lock.release()

    # 更新下载进度 刷新UI
    def change_title(self, total_num, current_num):
        self.title.set("已完成" + str(current_num) + "/" + str(total_num))

    # 生成失败列表
    def print_error(self, download_error_list):
        # python log
        print("-----------------------------------")
        print("some pic download failure:")
        for pic in download_error_list:
            print("")
            print("name:" + pic.name)
            print("url:" + pic.url)
            print("error_reason:" + pic.error_reason)

        Label(self.root, text="部分图片下载失败:").grid(row=4, column=1)

        # GUI
        # 新建listbox
        self.list_box = Listbox(self.root)
        for pic in download_error_list:
            self.list_box.insert(END, pic.url + " -> " + pic.error_reason)
        self.list_box.grid(row=5, column=0, columnspan=3, sticky=W+E+N+S)

        # 垂直 scrollbar
        scr1 = Scrollbar(self.root)
        self.list_box.configure(yscrollcommand=scr1.set)
        scr1['command'] = self.list_box.yview
        scr1.grid(row=5, column=4, sticky=W+E+N+S)
        # 水平 scrollbar
        scr2 = Scrollbar(self.root, orient='horizontal')
        self.list_box.configure(xscrollcommand=scr2.set)
        scr2['command'] = self.list_box.xview
        scr2.grid(row=6, column=0, columnspan=3, sticky=W+E+N+S)


dir_picker = XTImageDownloader()
