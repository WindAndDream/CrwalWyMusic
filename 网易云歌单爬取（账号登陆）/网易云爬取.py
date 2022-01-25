import json
import random
import threading
import time
import re
import requests
import os
import subprocess


# 获取歌单接口的响应信息
def getApiText():
    while True:
        try:
            print(f' ----  如果您是第一次使用本程序，请一定要记得先在网页端中登陆网易云账号，然后再添加cookie至本程序中  ---- ')
            print(f' ----  如果不明白怎么添加cookie，可百度或者私信我，我看见了就会回信息  ---- ')
            print(f' ----  如果你追求多线程速度，直接注释掉时间间隔就行了，不过你得注意下IP，并且需要代理  ---- ')
            playListId = input('请输入歌单id： ')
            prefixUrl = 'https://music.163.com/weapi/v6/playlist/detail?csrf_token='
            # 在dos命令符中用node.exe解析js文件，打开管道，将dos命令符中的输出结果变成这里的值
            if headers['cookie']:
                com = f'{os.getcwd()}/node.exe {os.getcwd()}/加密参数--歌单.js {playListId} {headers["cookie"].replace(" ", "")}'
                args = eval(subprocess.Popen(com, stdout=subprocess.PIPE).stdout.read().decode('utf-8'))
                # 表单参数
                reqData = {'params': args[0], 'encSecKey': args[1]}
                apiRes = requests.post(url=prefixUrl + args[2], headers=headers, data=reqData)
                # 转成json格式
                apiText = json.loads(apiRes.text)
                if apiText['code'] == 200:
                    return apiText
                else:
                    print(f' ----  请求接口的状态码为： {apiText["code"]}，您输入的歌单id有误，请重新输入  ---- ')
            else:
                print(f'您的cookie为： {headers["cookie"]}，请输入cookie！')
        except KeyError:
            # 在你登陆后，网易的cookie怎么说呢，接近半动态的感觉，时效好长，好长时间都不会有啥变化，一般来说都是动态才对的
            # 我看到有个16什么开头的，还以为是时间戳，结果也不是，反正要是cookie时效了你再加就行了
            print(f' ----  您没有添加cookie，请添加cookie  ---- ')
            print(f' ----  如果您已经添加了cookie，请检查cookie是否添加错误或已超出时效性，请重新添加  ---- ')


# 接收歌单接口的响应内容，这里是用来自己选择的范围歌曲内的所有信息
def divideSongRange(api_text):
    print(f"歌单名字： {api_text['playlist']['name']}")  # 歌单名字
    songLength, songInfoList = len(api_text['playlist']['tracks']), []  # 歌单长度, 歌单信息列表
    print(f"歌曲总数量： {songLength}首")  # 歌曲总数量
    for songNum, songInfo in enumerate(api_text['playlist']['tracks']):
        print(f"歌曲序号： {songNum + 1} | 歌曲名字： {songInfo['name']} | 歌曲id： {songInfo['id']} | "
              f"歌曲作者： {songInfo['ar'][0]['name']} | 歌曲专辑： {songInfo['al']['name']}")
        songInfoList.append({songNum + 1: [songInfo['id'], songInfo['name']]})  # 存储歌曲信息
    songScope = getSongScope(songLength)  # 歌曲的范围
    # return 对应范围的歌曲信息, 歌单名字
    return songInfoList[songScope[0] - 1: songScope[-1]], api_text['playlist']['name']


# 接收歌单歌曲总数量，返回范围
def getSongScope(song_length):
    while True:
        try:
            # 这里都是判断歌曲范围是否符合逻辑
            print(f'歌曲序号范围： 1~{song_length}')
            startNum, endNum = int(input('请输入起始爬取序号： ')), int(input('请输入结束爬取序号： '))
            if 0 < startNum <= endNum <= song_length and startNum <= song_length:
                return startNum, endNum
            else:
                print(f'您输入的起始序号为： {startNum}，结束序号为： {endNum}')
                print(f'（1）请输入大于1且小于或等于{song_length}的歌曲序号')
                print(f'（2）您的结束序号可能大于起始序号，请重新输入！')
                print(f'（3）您输入的序号可能为负数，请重新输入！')
        except ValueError:
            print(f'您输入的数并非整型数字，请重新输入！')


# 接收歌曲列表，划分列表，避免死锁，说白了就是把一阶列表转换为矩阵，[] --> [[], [], []...]
def nestList(song_list):
    divideNum, songListLength, divideSongResult = 0, len(song_list), []
    while True:
        if divideNum >= songListLength:
            divideSongResult.append(song_list[divideNum: songListLength])
            break
        # 这里的2其实可以改的哈，意思就是每爬2首歌就长时间暂停，你改多少就对应多少首歌长时间暂停
        divideSongResult.append(song_list[divideNum: divideNum + 2])
        divideNum += 2
    # 最后一个为空列表，扔掉就行了
    divideSongResult.pop()
    return divideSongResult


# 线程函数，获取每一首歌的接口内容
def getSongText(song_list_name, song_num, song_id, song_name):
    # 跟上面的大同小异，只不过传入的是歌曲id，打开管道，调用node解析js文件
    com = f'{os.getcwd()}/node.exe {os.getcwd()}/加密参数--歌曲.js {song_id}'
    encryParamList = eval(subprocess.Popen(com, stdout=subprocess.PIPE).stdout.read().decode('utf-8'))
    encryParamList = [encryParam.replace('\n', '') for encryParam in encryParamList]
    songApiUrl = 'https://music.163.com/weapi/song/enhance/player/url/v1?csrf_token='
    # 表单参数
    songFormData = {'params': encryParamList[0], 'encSecKey': encryParamList[1]}
    songRes = requests.post(url=songApiUrl, headers=headers, data=songFormData)
    # 转换json，作为实参传入saveSongUrls函数，毕竟线程函数没法return，声明全局变量来存储
    saveSongUrls(json.loads(songRes.text), song_num, song_name)
    print(f'歌单名字： {song_list_name} | 歌曲序号： {song_num} | 歌曲名字： {song_name} ----  请求成功  ---- ')


# 存储歌曲信息
def saveSongUrls(song_text, song_num, song_name):
    songUrls.append({song_num: [song_name, songInfo['url']] for songInfo in song_text['data']})


# 多线程调用
def multiThreadReqSong(song_info_list, song_list_name, multi_thread_function):
    threads = []
    # 列表里面嵌套两个字典，所以先遍历列表
    for songInfo in song_info_list:
        # 遍历字典
        for songNum, songBasicInfo in songInfo.items():
            # 添加线程对象
            threads.append(threading.Thread(target=multi_thread_function,
                                            args=(song_list_name, songNum, songBasicInfo[0], songBasicInfo[1])))
    # 启动线程
    for thread in threads:
        thread.start()
    # 终止线程
    for thread in threads:
        thread.join()
    # 时间间隔，追求速度的话，注释掉就行了，没代理还是老老实实等吧，不然IP被封也太无语了
    stayTime = random.choice([stay for stay in range(8, 15)])
    print(f'每一轮获取请求/保存的长时间暂停： {stayTime}秒')
    time.sleep(stayTime)


# 线程函数，保存音乐
def saveMusic(song_list_name, song_num, song_name, song_url):
    if song_url:
        songRes = requests.get(url=song_url, headers=headers)
        if songRes.status_code == 200:
            # 创建保存文件夹
            createSaveDir(song_list_name)
            with open(f'D:/爬虫专用文件夹/网易云音乐/【歌单】{song_list_name}/'
                      f'（{song_num}）{delSpecChar(song_name)}.mp3', 'wb') as f:
                f.write(songRes.content)
                print(f'歌单名字： {song_list_name} | D:/爬虫专用文件夹/网易云音乐/【歌单】{song_list_name}/'
                      f'{delSpecChar(song_name)}.mp3 ----  保存成功  ---- ')
        else:
            print(f'歌单名字： {song_list_name} | 请求状态码： {songRes.status_code} | D:/爬虫专用文件夹/网易云音乐/【歌单'
                  f'】{song_list_name}/{delSpecChar(song_name)}.mp3 ----  保存失败  ---- ')
    else:
        print(f'歌单名字： {song_list_name} | 歌曲序号： {song_num} | 歌曲名字： {song_name} ----  为付费音乐或特殊原因无法下载  ---- ')


# 创建文件夹
def createSaveDir(song_list_name):
    if not os.path.exists(f'D:/爬虫专用文件夹/网易云音乐/【歌单】{delSpecChar(song_list_name)}'):
        os.makedirs(f'D:/爬虫专用文件夹/网易云音乐/【歌单】{delSpecChar(song_list_name)}')
        print(f'D:/爬虫专用文件夹/网易云音乐/【歌单】{delSpecChar(song_list_name)} ----  保存文件夹创建成功  ---- ')


# 删除特殊字符，避免无法创建文件夹或文件
def delSpecChar(string):
    return re.sub(r'[\\/:*?"<>|]', '', string)


def main():
    # 获取歌单接口响应内容
    apiText = getApiText()
    # songRange = ([{歌曲序号: [歌曲id, 歌曲名字]}, {..}, {..}...], 歌单名字)
    songRange = divideSongRange(apiText)
    # songList = [[{歌曲序号: [歌曲id, 歌曲名字]}, {歌曲序号: [歌曲id, 歌曲名字]}], [..], [..]...]
    songList = nestList(songRange[0])
    # song = [{歌曲序号: [歌曲id, 歌曲名字]}, {歌曲序号: [歌曲id, 歌曲名字]}]...
    for song in songList:
        # songUrls = [{歌曲序号: [歌曲名字, 歌曲url]}, {歌曲序号: [歌曲名字, 歌曲url]}]...
        global songUrls
        # 多线程获取每首歌的接口内容
        multiThreadReqSong(song, songRange[1], getSongText)
        # 多线程请求每首歌的url，同时保存
        multiThreadReqSong(songUrls, songRange[1], saveMusic)
        # 把songUrls清空，不然下一轮会累加上一轮循环的内容
        songUrls = []
    print(f'歌单： {songRange[1]}  ---- 爬取完成  ---- ')


if __name__ == '__main__':
    # 请记得添加cookie
    headers, songUrls = {
                            'User-Agent': 'Mozilla/5.0',
                            'cookie': ''
                        }, []
    main()
