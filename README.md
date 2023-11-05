# Python Service: Configuration & Discovery & Log
基于python构建的配置·服务发现·日志查看中心。
## Center
基于fastAPI，基于http等rpc方式提供配置、服务发现、日志收集
## Discovery
## Log
将标准输出额外地异步输出到网络
## Configuration
将配置基于json形式分发给所需服务
## 预期支持的RPC方式
- HTTP短轮询
- HTTP长轮询
- WebSocket
- gRPC

## 业务模型
- serviceInstance：服务实例
- serverConfig：服务器配置
- 
## 技术模型
- 服务端
  - 持久化:
    - 内存
    - FS
    - 数据库
- 客户端
  - 客户端基于异步+队列维护所有任务，不占用主线程。

## http长轮询业务设计方案
http长轮询之优点在于不必像WebSocket一样维护长久生命周期，同时继承了http无状态的优点，又不必像http短轮询一样过分消耗性能。
对于http长轮询，期望每5~30s重建连接。客户端必须假设服务器随时可能断开连接。
### 日志收集
由客户端向服务端建立http请求：在body中以plain/text形式输出日志。
在未发送成功时，客户端缓存日志。
