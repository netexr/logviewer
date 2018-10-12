## 说明
这是一个测试环境查看日志的web工具，当初公司的测试环境部署了多个tomcat，为了不让尽量不让开发登陆服务，所以开发了这个工具。

- 根据规则遍历指定目录下的tomcat应用
- 进入应用遍历所有的日志文件，然后选择文件进行日志查看
- 每页默认展示1M大小的文件（太大会导致浏览器卡死），支持翻页和简单的搜索
- 支持CAS登陆
- 支持下载和清空文件

### 使用方式
```bash
# 使用前先修改下pid和日志路径
./control.sh [start|stop|reload|restart]"
```
