# takungpao download 
# git clone https://github.com/bj5/takungpao_download 
# pip install  bs4 PyPDF2
# python takungpao_download.py
# or python takungpao_download.py -date 20250101
# 
import os
import random
import time
import requests
import re
import sys
import argparse
import shutil

from datetime import datetime, timedelta
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from PyPDF2 import PdfMerger



def extract_ab_numbers(text):
    # 正则表达式：匹配a或b后跟1-2位数字
    pattern = r'[ABCabc]\d{1,2}'
    matches = re.findall(pattern, text)
    return matches
    

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
]

def get_takungpao_hk_pdfs(date_str):
    base_url = f"http://www.takungpao.com.hk/paper/list-{date_str}.html"
    
    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Referer': 'http://www.takungpao.com.hk/',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Connection': 'keep-alive'
    }

    def safe_request(url, headers=headers, max_retries=3, timeout=30):
        retries = 0
        while retries < max_retries:
            try:
                response = requests.get(url, headers=headers, timeout=timeout)
                response.raise_for_status()
                return response
            except (requests.exceptions.RequestException, ConnectionResetError) as e:
                print(f"请求失败（重试 {retries+1}/{max_retries}）: {url} - {str(e)}")
                retries += 1
                time.sleep(2**retries)
        return None

    try:
        # 获取电子版主页
        response = safe_request(base_url)
        if not response:
            raise Exception("无法获取电子版主页")
        
        soup = BeautifulSoup(response.text, 'html.parser')
      
        
        # 提取所有img的alt属性（关键部分）
        img_alt_list = []
        pdf_links = []
        for img_tag in soup.find_all('img'):
            alt_text = img_tag.get('alt', '无alt属性')
            if alt_text.strip():  # 过滤空值
                img_alt_list.append(alt_text)
                print(f"找到img的alt属性：{extract_ab_numbers(alt_text)}")
                #https://paper.takungpao.com/resfile/PDF/20250326/PDF/a12_screen.pdf
                matches = extract_ab_numbers(alt_text)
                if matches:
                    print(matches[0])
                    print(f"https://paper.takungpao.com/resfile/PDF/{date_str}/PDF/{matches[0].lower()}_screen.pdf")
                    pdf_links.append(f"https://paper.takungpao.com/resfile/PDF/{date_str}/PDF/{matches[0].lower()}_screen.pdf")
    
                else:
                    print("未找到匹配项")
                
        uniq_pdf_links = list(dict.fromkeys(pdf_links))        
        

        # 创建临时目录保存PDF文件
        temp_dir = f"temp_pdfs_{date_str}"
        os.makedirs(temp_dir, exist_ok=True)

        pdf_files = []
        for link in uniq_pdf_links:
            try:
                time.sleep(random.uniform(1, 3))
                response = safe_request(link)
                if not response:
                    print(f"下载失败（重试耗尽）: {link}")
                    continue
                
                filename = os.path.join(temp_dir, os.path.basename(link))
                with open(filename, 'wb') as f:
                    f.write(response.content)
                pdf_files.append(filename)
                print(f"成功下载: {filename}")
            except Exception as e:
                print(f"下载失败: {link} - {str(e)}")

        # 合并PDF文件
        if pdf_files:
            merger = PdfMerger()
            #pdf_files.sort(key=lambda x: int(os.path.splitext(os.path.basename(x))[0].split('_')[-1]))
            
            for pdf in pdf_files:
                merger.append(pdf)
            
            output_filename = f"大公报香港版_{date_str}.pdf"
            with open(output_filename, 'wb') as f:
                merger.write(f)
            
            print(f"合并完成：{output_filename}")
            
            
            merger.close()
            
            
            # 清理临时文件
            for file in pdf_files:
                os.remove(file)
            os.rmdir(temp_dir)
            #shutil.rmtree(temp_dir)
        else:
            print("未找到可下载的PDF文件")

        # 返回或保存img的alt属性（示例：打印所有alt文本）
        # print("\n所有提取的img alt属性：")
        # for alt in img_alt_list:
        #    print(alt)

    except Exception as e:
        print(f"程序异常：{str(e)}")

if __name__ == "__main__":
    now = datetime.now()
    end_date = now
    argc = len(sys.argv)
    start_date = now
    if argc > 1:
        argv = sys.argv[1:]
        parser = argparse.ArgumentParser(description='ArgUtils')
        parser.add_argument('-date', type=str, default=None, help="start date")
        parser.add_argument('--date', type=str, default=None, help="start date")
        args = parser.parse_args()
        if args.date:
            start_str = "{}{}{}".format(args.date[0:4], args.date[4:6], args.date[6:8])
            try:
                start_date = datetime.strptime(start_str, "%Y%m%d")
            except ValueError:
                print(f"无效的日期格式: {args.date}. 使用YYYYMMDD格式。")
                sys.exit(1)
    
    current = start_date
    while current <= end_date:
        date_str = current.strftime("%Y%m%d")
        print(f"处理日期: {date_str}")
        get_takungpao_hk_pdfs(date_str)
        current += timedelta(days=1)