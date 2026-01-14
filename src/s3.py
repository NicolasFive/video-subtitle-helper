# s3_signer.py
import hashlib
import hmac
import base64
import datetime
import urllib.parse
from email.utils import formatdate
import requests

class S3Operator:
    def __init__(self, endpoint, access_key, secret_key, bucket):
        self.endpoint = endpoint.rstrip('/')
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket = bucket
        self.host = urllib.parse.urlparse(endpoint).netloc
        
    def generate_date_header(self):
        """生成日期头"""
        return formatdate(timeval=None, localtime=False, usegmt=True)
    
    def simple_sign(self, method, content_type="", object_key=""):
        """生成简化签名（适用于S3兼容服务）"""
        date_header = self.generate_date_header()
        
        # 构建签名字符串
        string_to_sign = f"{method}\n\n{content_type}\n{date_header}\n/{self.bucket}/{object_key}"
        
        # 计算签名
        signature = base64.b64encode(
            hmac.new(
                self.secret_key.encode('utf-8'),
                string_to_sign.encode('utf-8'),
                hashlib.sha1
            ).digest()
        ).decode('utf-8')
        
        return date_header, signature
    
    def upload(self, object_key, file_path):
        date_header, signature = self.simple_sign("PUT", "text/plain", object_key)
        # 构建请求 URL
        url = f"{self.endpoint}/{self.bucket}/{object_key}"
        # 构建请求头
        headers = {
            "Host": self.host,
            "Date": date_header,
            "Content-Type": "text/plain",
            "Authorization": f"AWS {self.access_key}:{signature}"
        }
        # 读取文件内容
        with open(file_path, 'rb') as f:
            file_content = f.read()

        # 发送 PUT 请求
        response = requests.put(
            url=url,
            headers=headers,
            data=file_content
        )
        if response.status_code == 200:  
            return f"{self.endpoint}/{self.bucket}/{object_key}"
        else:
            return response.text
    
    def download(self, object_key, output_file):
        date_header, signature = self.simple_sign("GET", "", object_key)
        # 构建请求 URL
        url = f"{self.endpoint}/{self.bucket}/{object_key}"
        # 构建请求头
        headers = {
            "Host": self.host,
            "Date": date_header,
            "Authorization": f"AWS {self.access_key}:{signature}"
        }
        # 发送 GET 请求
        response = requests.get(
            url=url,
            headers=headers,
            stream=True  # 启用流式下载
        )
        if response.status_code == 200:  
            return output_file
        else:
            return response.text
    
    def delete(self, object_key):
        date_header, signature = self.simple_sign("DELETE", "", object_key)
        # 构建请求 URL
        url = f"{self.endpoint}/{self.bucket}/{object_key}"
        # 构建请求头
        headers = {
            "Host": self.host,
            "Date": date_header,
            "Authorization": f"AWS {self.access_key}:{signature}"
        }
        # 发送 DELETE 请求
        response = requests.delete(
            url=url,
            headers=headers
        )
        if response.status_code == 200:  
            return "success"
        else:
            return response.text
    