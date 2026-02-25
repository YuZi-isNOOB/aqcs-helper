import asyncio
import aiohttp
import struct
import hashlib
import xml.etree.ElementTree as ET
import time
import os
import json
import random
import sys
import msvcrt

# ================= HTTP协程 =================
class HttpClientAsync:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip("/")

    async def post_form(self, path, data, headers=None):
        async with aiohttp.ClientSession() as session:
            async with session.post(self.base_url + path, data=data, headers=headers) as resp:
                text = await resp.text()
                return self.parse_response(text)

    def parse_response(self, xml_text):
        root = ET.fromstring(xml_text)
        return {child.tag: child.text for child in root}

class ReadLoginBack:
    def __init__(self, hex_data: str):
        self.data = bytes.fromhex(hex_data)
        self.pos = 0
        self.result = {}

    # 基础读取函数
    def read_u8(self):
        v = self.data[self.pos]
        self.pos += 1
        return v

    def read_u16(self):
        v = struct.unpack(">H", self.data[self.pos:self.pos+2])[0]
        self.pos += 2
        return v

    def read_u32(self):
        v = struct.unpack(">I", self.data[self.pos:self.pos+4])[0]
        self.pos += 4
        return v

    def read_str(self):
        length = self.read_u8()
        # print("str长度：", length)
        s = self.data[self.pos:self.pos+(length-1)//2].decode("utf-8")
        # print("str：", s)
        self.pos += length//2
        return s

    def read_asmess(self):
        sign = self.read_u8()
        if sign == 1:
            self.pos += 1
            return None
        elif sign == 2:
            self.pos += 1
            return False
        elif sign == 3:
            self.pos += 1
            return True
        elif sign == 4:
            result = 0
            for i in range(4):
                b = int.from_bytes(self.data[self.pos:self.pos+1])
                # print(b)
                self.pos += 1
                if i < 3:
                    result <<= 7
                    result |= (b & 0x7F)
                    if not (b & 0x80):
                        return result
                else:
                    result <<= 8
                    result |= b
                    return result
            return result
        elif sign == 5:
            date = struct.unpack(">d", self.data[self.pos:self.pos+8])[0]
            self.pos += 8
            return date
        elif sign == 6:
            length = self.read_u8()
            s = self.data[self.pos:self.pos+length//2].decode("utf-8")
            self.pos += length//2
            return s
        
    def parse(self):
        self.result['total_len'] = self.read_u32()
        # 读取头部
        self.result['header'] = self.read_u32()
        str1 = self.read_str()
        str2 = self.read_str()
        str3 = self.read_str()
        str4 = self.read_str()
        # 字段lastLoginTime
        self.result[str1] = self.read_asmess()
        # 字段_cmd
        self.result[str2] = self.read_asmess()
        # 字段id
        self.result[str3] = self.read_asmess()
        # 字段n
        self.result[str4] = self.read_asmess()
        return self.result
    

# ================= Socket Client =================
class FlashClientAsync:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.reader = None
        self.writer = None
        self.packet_num = 0
        self._listen_running = False

    # -------------------------
    # 初始化用户信息（协程）
    # -------------------------
    async def init_user_info(self, send, lastlogintime, delay=0.3):
        items = [
            {"id": 2, "cmd": "2_39_0"},
            {"id": 25, "cmd": "25_2_1"},
            {"id": 3, "cmd": "3_1_1"},
            {"id": 3, "cmd": "3_11"},
            {"id": 6, "cmd": "6_0"},
            {"id": 2, "cmd": "2_1_10"},
            {"id": 11, "cmd": "11_1"},
            {"id": 21, "cmd": "21_1"},
            {"id": 25, "cmd": "25_3"},
            {"id": 2, "cmd": "2_2_10"},
            {"id": 2, "cmd": "2_0_1"},
            {"id": 17, "cmd": "17_9"},
            {"id": 76, "cmd": "76_A"},
            {"id": 2, "cmd": "2_1_K"},
            {"id": 21, "cmd": "21_0_A"},
            {"id": 37, "cmd": "37_177_1"},
            {"id": 27, "cmd": "27_1"},
            {"id": 30, "cmd": "30_1"},
            {"id": 30, "cmd": "30_1_1"},
            {"id": 3, "cmd": "3_4_0"},
            {"id": 129, "cmd": "129_0"},
            {"id": 60, "cmd": "60_A"},
            {"id": 117, "cmd": "117_1"},
            {"id": 111, "cmd": "111_2"},
            {"id": 3, "cmd": "3_5_1"},
        ]

        t = random.uniform(delay, 1.5)

        await self.send_bytes(send.sendXtMessage(-1, {
            "id": 13, "cmd": "13_1", "param": {}
        }))
        await asyncio.sleep(t)

        await self.send_bytes(send.sendXtMessage(-1, {
            "id": 1,
            "cmd": "getStartInfo",
            "param": {
                'firstLogin': False,
                'lastLoginTime': lastlogintime,
                'di': 'PC#Blink#360SE#',
                'pi': 2
            }
        }))
        await asyncio.sleep(t)

        await self.send_bytes(send.sendXtMessage(-1, {
            "id": 1,
            "cmd": "getCurrentTime",
            "param": {}
        }))
        await asyncio.sleep(t)

        for item in items:
            await self.send_bytes(send.sendXtMessage(-1, {
                "id": item["id"],
                "cmd": item["cmd"],
                "param": {}
            }))
            await asyncio.sleep(t)
        

    # -------------------------
    # 进入房间（协程）
    # -------------------------
    async def enter_main_hut(self, send, mainAccount, thisAccount, delay=0.3):
        roomname = mainAccount + '_1_Home1'
        enter_cmd = "539,314,0,0," + roomname + "," + thisAccount
        enter_cmd_2 = "539,314,1,0," + roomname + "," + thisAccount
        # transform_1 = "314,306,1,110," + roomname + "," + thisAccount
        # transform_2 = "613,329,1,110," + roomname + "," + thisAccount
        t = random.uniform(delay, 1.5)

        await self.send_bytes(send.sendXtMessage(-1, {
            "id": 26, "cmd": "26_1_1",
            "param": {'p': 1, 'un': mainAccount}
        }))
        await asyncio.sleep(t)

        await self.send_bytes(send.sendXtMessage(-1, {
            "id": 26, "cmd": "26_4",
            "param": {'m': mainAccount}
        }))
        await asyncio.sleep(t)

        await self.send_bytes(send.sendXtMessage(-1, {
            "id": 1, "cmd": "creatJoinRoom",
            "param": {'r': roomname}
        }))
        await asyncio.sleep(t)

        await self.send_bytes(send.sendXtMessageByte(
            "00272c00011ed1000100027074730027" + enter_cmd.encode().hex()
        ))
        await asyncio.sleep(t)

        await self.send_bytes(send.sendXtMessageByte(
            "00272c00011ed1000100027074730027" + enter_cmd_2.encode().hex()
        ))
        await asyncio.sleep(t)
        for _ in range(35):
            transform_1 = str(random.randint(100, 800)) + "," + str(random.randint(280, 380)) + ",1,110," + roomname + "," + thisAccount
            await self.send_bytes(send.sendXtMessageByte(
                "00272c00011cf1000100027074730029" + transform_1.encode().hex()
            ))
            await asyncio.sleep(10) # 走两步

    async def alliance_daily(self, send, delay = 0.3):
        t = random.uniform(delay, 1.5)
        await self.send_bytes(send.sendXtMessage(-1, {
            "id": 1015, "cmd": "1015_1_2",
            "param": {'ci': 2}
        }))
        await asyncio.sleep(t)
        count = 0
        while count < 3:
            # 摇吉：发送并接收（防止花钻石）
            await self.send_bytes(send.sendXtMessage(-1, {
                "id": 1016, "cmd": "1016_5_1",
                "param": {}
            }))
            # 启动监听
            # 指定你想匹配的字节序列
            match_hex = "72616e6b73057074096d777763095f636d64057763"
            match_bytes = bytes.fromhex(match_hex)
            packet = await self.listen_raw(match_bytes)
            count += 1
            print("剩余免费次数（免费3次）:", 3 - packet[-15])
            if packet[-15] > 2:
                break
            elif packet[-1] == 6:
                break
            await self.send_bytes(send.sendXtMessage(-1, {
                "id": 1016, "cmd": "1016_5_2",
                "param": {'ci': 6}
            }))
            print("ok")
            await asyncio.sleep(t)
        # 转轮
        for _ in range(5):
            await self.send_bytes(send.sendXtMessage(-1, {
                "id": 1016, "cmd": "1016_6_4",
                "param": {}
            }))
            await asyncio.sleep(t)
        for _ in range(5):
            await self.send_bytes(send.sendXtMessage(-1, {
                "id": 1016, "cmd": "1016_6_2",
                "param": {'ci': 2, 'iok': False, 'tid': 2}
            }))
            await asyncio.sleep(t)
            await self.send_bytes(send.sendXtMessage(-1, {
                "id": 1016, "cmd": "1016_6_2",
                "param": {'ci': 2, 'iok': False, 'tid': 1}
            }))
            await asyncio.sleep(t)
        await self.send_bytes(send.sendXtMessage(-1, {
            "id": 1015, "cmd": "1015_4_3",
            "param": {'ec': 1, 'ci': 2, 'gid': 18}
        }))
        await asyncio.sleep(t)
    async def daily(self, send, delay = 0.3):
        t = random.uniform(delay, 1.5)
        await self.send_bytes(send.sendXtMessage(-1, {
            "id": 1008,
            "cmd": "1008_20250403_montab1_2",
            "param": {'ci': 2}
        }))
        await asyncio.sleep(t) # 登录1钻石+15
        await self.send_bytes(send.sendXtMessage(-1, {
            "id": 1008,
            "cmd": "1008_20250613_nzymj5",
            "param": {'an': 1}
        }))
        await asyncio.sleep(t) # 每日竞猜一次+30
        await self.send_bytes(send.sendXtMessage(-1, {
            "id": 1008,
            "cmd": "1008_20250613_nzymj1",
            "param": {}
        }))
        await asyncio.sleep(t) # 每日竞猜
        for _ in range(15):
            await self.send_bytes(send.sendXtMessage(-1, {
                "id": 1008,
                "cmd": "1008_20250613_nzymj2",
                "param": {'i': 1, 'l': '0'}
            }))
            await asyncio.sleep(t) # 每日竞猜
        await self.send_bytes(send.sendXtMessage(-1, {
            "id": 1008,
            "cmd": "1008_20250613_nzymj3",
            "param": {'p': False}
        }))
        await asyncio.sleep(t) # 每日竞猜
        await self.send_bytes(send.sendXtMessage(-1, {
            "id": 1019,
            "cmd": "1019_1",
            "param": {'ci': 2, 'ai': 4852, 'bi': 9}
        }))
        await asyncio.sleep(t) # 每日竞猜换金币
        
        await self.send_bytes(send.sendXtMessage(-1, {
            "id": 1008,
            "cmd": "1008_20190531_gbt_4",
            "param": {'ci': 2, 'iok': False}
        }))
        await asyncio.sleep(t)
        await self.send_bytes(send.sendXtMessage(-1, {
            "id": 1008,
            "cmd": "1008_20190531_gbt_3",
            "param": {}
        }))
        await asyncio.sleep(t) # 每日采摘缤纷树+15

        countys = 0
        while countys < 5:
            await self.send_bytes(send.sendXtMessage(-1, {
                "id": 2,
                "cmd": "2_36_1",
                "param": {}
            }))
            await asyncio.sleep(t) # 每日1次源兽捕捉+15
            match_hex_ys = "05636305626305616307766f6b0963636c74095f636d640762786c07777074096e627074057763057774057463"
            match_bytes_ys = bytes.fromhex(match_hex_ys)
            packet_ys = await self.listen_raw(match_bytes_ys, 20)
            countys += 1
            if (packet_ys is None):
                print("未收到源兽捕捉返回包，可能是连接问题，停止监听")
                return
            freetime_ys = int(packet_ys[-1])
            print(f"源兽捕捉完成：{freetime_ys}次")
            if (freetime_ys != 0):
                break
            await self.send_bytes(send.sendXtMessage(-1, {
                "id": 2,
                "cmd": "2_36_8",
                "param": {'ci': 4}
            }))
            await asyncio.sleep(t) # 每日1次源兽捕捉+15
        
        count = 0
        while count < 5:
            await self.send_bytes(send.sendXtMessage(-1, {
                "id": 1008,
                "cmd": "1008_20220603_swa_0_0",
                "param": {}
            }))
            await asyncio.sleep(t) # 每日1次星轮探险+15
            match_hex = "0764677407777470037207766f6b07776774095f636d64"
            match_bytes = bytes.fromhex(match_hex)
            packet = await self.listen_raw(match_bytes, 20)
            count += 1
            if (packet is None):
                print(f"{count}次未收到星轮探险返回包，可能是连接问题，停止监听")
                continue
            idx = packet.find(match_bytes)
            freetime = int(packet[idx + len(match_bytes) + 1])
            print(f"星轮探险完成：{freetime}次")
            if (freetime != 0):
                break
            await self.send_bytes(send.sendXtMessage(-1, {
                "id": 1008,
                "cmd": "1008_20220603_swa_0_3",
                "param": {'ci': 2}
            }))
            await asyncio.sleep(t) # 每日1次星轮探险+15
        await self.send_bytes(send.sendXtMessage(-1, {
            "id": 1008,
            "cmd": "1008_20170623_dt_1",
            "param": {'bi': 0, 'ci': 2}
        }))
        await asyncio.sleep(t) # 领取每日任务
        await self.send_bytes(send.sendXtMessage(-1, {
            "id": 1008,
            "cmd": "1008_20190301_am_3",
            "param": {'id': 0, 'ci': 2}
        }))
        await asyncio.sleep(t) # 元宝兑换钻石
    async def sayhello(self, send, mainAccount, delay = 0.3):
        t = random.uniform(delay, 1.5)
        await self.send_bytes(send.sendXtMessage(-1, {
            "id": 25,
            "cmd": "25_20",
            "param": {'ci': 2, 'm': 'Hello~!', 'b': mainAccount}
        }))
        await asyncio.sleep(t) # 打招呼加亲密度20
    async def intimacy(self, send, mainAccount, delay = 0.3):
        t = random.uniform(delay, 1.5)
        await self.send_bytes(send.sendXtMessage(-1, {
            "id": 25,
            "cmd": "25_1_3",
            "param": {'c': 3, 'gi': 3, 'run': mainAccount}
        }))
        await asyncio.sleep(t) # 每周10w经验果，2级亲密度
        for _ in range(3):
            await self.send_bytes(send.sendXtMessage(-1, {
                "id": 25,
                "cmd": "25_1_3",
                "param": {'c': 1, 'gi': 3, 'run': mainAccount}
            }))
            await asyncio.sleep(t) # 每周10w经验果，2级亲密度
        await self.send_bytes(send.sendXtMessage(-1, {
            "id": 25,
            "cmd": "25_1_3",
            "param": {'c': 3, 'gi': 4, 'run': mainAccount}
        }))
        await asyncio.sleep(t) # 每周2x潜能果，2级亲密度
        for _ in range(3):
            await self.send_bytes(send.sendXtMessage(-1, {
                "id": 25,
                "cmd": "25_1_3",
                "param": {'c': 1, 'gi': 4, 'run': mainAccount}
            }))
            await asyncio.sleep(t) # 每周2x潜能果，2级亲密度
        await self.send_bytes(send.sendXtMessage(-1, {
            "id": 25,
            "cmd": "25_1_3",
            "param": {'c': 2, 'gi': 0, 'run': mainAccount}
        }))
        await asyncio.sleep(t) # 每周大星元，3级亲密度
        for _ in range(2):
            await self.send_bytes(send.sendXtMessage(-1, {
                "id": 25,
                "cmd": "25_1_3",
                "param": {'c': 1, 'gi': 0, 'run': mainAccount}
            }))
            await asyncio.sleep(t) # 每周大星元，3级亲密度
        await self.send_bytes(send.sendXtMessage(-1, {
            "id": 25,
            "cmd": "25_1_3",
            "param": {'c': 3, 'gi': 5, 'run': mainAccount}
        }))
        await asyncio.sleep(t) # 每周源兽，3级亲密度
        for _ in range(3):
            await self.send_bytes(send.sendXtMessage(-1, {
                "id": 25,
                "cmd": "25_1_3",
                "param": {'c': 1, 'gi': 5, 'run': mainAccount}
            }))
            await asyncio.sleep(t) # 每周源兽，3级亲密度
    async def mainAccount(self, send, delay = 0.3):
        t = random.uniform(delay, 1.5)
        print("ceshikaishi")
        await asyncio.sleep(5)
        await self.send_bytes(send.sendXtMessage(-1, {
            "id": 25,
            "cmd": "25_1_1",
            "param": {}
        }))
        await asyncio.sleep(t) # 测试主账号领取 自己h5领取更好
        # for i in range(99, 28, -1):
        #     await self.send_bytes(send.sendXtMessage(-1, {
        #         "id": 25,
        #         "cmd": "25_1_4",
        #         "param": {'gi': f'83177{i:02d}', 'ci': 2}
        #     }))
        #     await asyncio.sleep(t) # 测试主账号领取
    # -------------------------
    # 连接服务器
    # -------------------------
    async def connect(self):
        self.reader, self.writer = await asyncio.open_connection(self.ip, self.port)
        await self._read_policy()

    async def _read_policy(self):
        while True:
            b = await self.reader.read(1)
            if b == b'\x00':
                break

    # -------------------------
    # XOR 加密算法
    # -------------------------
    def encrypt_flash(self, payload_bytes):
        key = struct.pack(">I", self.packet_num)
        encrypted = bytearray()
        key_len = len(key)

        for i, b in enumerate(payload_bytes):
            encrypted.append(b ^ key[i % key_len])
        return encrypted

    # -------------------------
    # Binary 写入方法
    # -------------------------
    def write_utf(self, ba, string):
        utf_bytes = string.encode("utf-8")
        ba.extend(struct.pack(">H", len(utf_bytes)))
        ba.extend(utf_bytes)

    def write_short(self, ba, value):
        ba.extend(struct.pack(">h", value))

    def write_int(self, ba, value):
        ba.extend(struct.pack(">i", value))

    def write_byte(self, ba, value):
        ba.extend(struct.pack(">b", value))

    # -------------------------
    # 构造登录包
    # -------------------------
    def build_login_packet(self, zone, username, password):
        data = bytearray()
        self.write_byte(data, 0)
        self.write_short(data, 10016)
        self.write_int(data, -1)

        for s in (zone, username, password):
            self.write_utf(data, s)

        encrypted = self.encrypt_flash(data)

        final = struct.pack(">I", len(data) + 4)
        final += struct.pack(">I", self.packet_num)
        final += encrypted
        return final

    # -------------------------
    # 登录（协程）
    # -------------------------
    async def login(self, zone, username, password):
        packet = self.build_login_packet(zone, username, password)
        await self.send_bytes(packet)

        match_hex = "6c6173744c6f67696e54696d65095f636d64056964036e"
        match_bytes = bytes.fromhex(match_hex)
        resp = await self.listen_raw(match_bytes, 10)

        # resp = await self.reader.read(4096)
        # print("RAW HEX:", resp.hex())
        parser = ReadLoginBack(resp.hex())
        return parser.parse()

    # -------------------------
    # 发送数据（协程）
    # -------------------------
    async def send_bytes(self, data: bytes):
        if not self.writer:
            print("Socket 未连接")
            return
        self.writer.write(data)
        await self.writer.drain()
    # -------------------------
    # 接收原始 TCP 包（不解密、不解析）
    # -------------------------
    async def recv_raw_packet(self):
        if not self.reader:
            print("Socket 未连接")
            return None

        try:
            # 先读长度字段（4字节大端）
            len_bytes = await self.reader.readexactly(4)
            total_len = struct.unpack(">I", len_bytes)[0]

            # 再读剩余数据
            payload = await self.reader.readexactly(total_len)
            return len_bytes + payload  # 返回完整原始包
        except asyncio.IncompleteReadError:
            print("服务器关闭连接")
            return None

    # 持续监听
    async def listen_raw(self, match_bytes: bytes = None, timeout: float = 30):
        """
        最多监听 timeout 秒（总时间）
        """
        self._listen_running = True
        start_time = time.monotonic()

        try:
            while self._listen_running:
                remaining = timeout - (time.monotonic() - start_time)
                if remaining <= 0:
                    print("监听总超时")
                    return None

                try:
                    packet = await asyncio.wait_for(
                        self.recv_raw_packet(),
                        timeout=remaining
                    )
                except asyncio.TimeoutError:
                    print("监听超时")
                    return None

                if packet is None:
                    return None

                if match_bytes is None or match_bytes in packet:
                    return packet

                await asyncio.sleep(0)

        finally:
            self._listen_running = False
    # -------------------------
    # 停止监听
    # -------------------------
    def stop_listen(self):
        self._listen_running = False

    async def close(self):
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
            self.writer = None

class MsgSeq:
    def __init__(self, s: str):
        self.num1 = 2
        self.num2 = 653
        self.num3 = 471
        self.num4 = 1
        self._hashSessionId = self.hash_as3(s)
        self._isFirstTime = True
        # print(self._hashSessionId)
    def mod_as3(self, dividend: int, divisor: int) -> int:
        r = dividend % divisor
        if dividend < 0 and r > 0:
            r -= abs(divisor)
        return r
    def next(self, arg1: int, arg2: int) -> int:
        # 第一次调用且 arg1 为 0
        if arg1 == 0 and self._isFirstTime:
            self._isFirstTime = False
            return 79

        # 主计算逻辑
        local3 = (arg1 * self.num1) + self.mod_as3(arg2, self.num2) + self.mod_as3(self._hashSessionId, self.num3)
        # print(self.mod_as3(self._hashSessionId, self.num3))
        # 超过 2147483647 处理
        if local3 >= 2147483647:
            local3 = self.mod_as3(local3, 1047483647) + self.num4

        local3 = self.as3_int32(local3)

        return local3

    def as3_int32(self, val: int) -> int:
        val = val & 0xFFFFFFFF  # 保留低 32 位
        if val >= 0x80000000:   # 如果超过 2^31-1，转换为负数
            val -= 0x100000000
        return val
    
    def hash_as3(self, s: str) -> int:
        result = 0
        for c in s:
            result = self.as3_int32(31 * result + ord(c))
        return result

class SendMessage:
    def __init__(self):
        self.buf = bytearray()
        self.msgNoObj = {}
        self.inited = False
        self.seed = 0
        self.userId = 0
        self.packet_num = 0
    def setmsgseq(self, s: str):
        self.msgseq = MsgSeq(s)
    def setUserId(self, userid: int):
        self.userId = int(userid)
        return self.userId
    # ================= 基础写入 =================
    def writeByte(self, v: int):
        self.buf.append(v & 0xFF)

    def writeShort(self, v: int):
        self.buf += struct.pack(">h", v)

    def writeInt(self, v: int):
        self.buf += struct.pack(">i", v)

    def writeUTF(self, s: str):
        data = s.encode("utf-8")
        self.buf += struct.pack(">H", len(data))
        self.buf += data

    # ================= AMF3 writeObject =================
    def writeObject(self, obj):
        if isinstance(obj, bool):
            # AMF3 boolean
            self.writeByte(0x03 if obj else 0x02)  # 0x03 = true, 0x02 = false

        elif isinstance(obj, int):
            if -268435456 <= obj <= 268435455:
                self.writeAMFInt(obj)
            else:
                self.writeAMFDouble(obj)

        elif isinstance(obj, float):
            self.writeAMFDouble(obj)

        elif isinstance(obj, str):
            self.writeAMFString(obj)

        elif isinstance(obj, dict):
            self.writeAMFDict(obj)

        elif isinstance(obj, (bytes, bytearray)):
            self.writeAMFByteArray(obj)

        else:
            raise TypeError("unsupported type: " + str(type(obj)))


    def writeAMFInt(self, v):
        self.writeByte(0x04)  # int marker
        self.writeU29(v & 0x1FFFFFFF)

    def writeAMFString(self, s):
        self.writeByte(0x06)  # string marker
        data = s.encode("utf-8")
        self.writeU29((len(data) << 1) | 1)
        self.buf += data

    def writeAMFDict(self, d: dict):
        self.writeByte(0x0A)   # object marker
        self.writeU29(0x0B)    # inline, dynamic, no sealed

        self.writeAMFStringRaw("")

        for k, v in d.items():
            self.writeAMFStringRaw(k)
            self.writeObject(v)

        # end of dynamic members
        self.writeAMFStringRaw("")

    def writeAMFStringRaw(self, s):
        data = s.encode("utf-8")
        self.writeU29((len(data) << 1) | 1)
        self.buf += data
    def writeAMFByteArray(self, b: bytes):
        self.writeByte(0x0C)  # ByteArray marker
        self.writeU29((len(b) << 1) | 1)
        self.buf += b
    def writeAMFDouble(self, v):
        self.writeByte(0x05)  # double marker
        self.buf += struct.pack(">d", float(v))

    def writeU29(self, v):
        if v < 0x80:
            self.writeByte(v)
        elif v < 0x4000:
            self.writeByte(((v >> 7) & 0x7F) | 0x80)
            self.writeByte(v & 0x7F)
        elif v < 0x200000:
            self.writeByte(((v >> 14) & 0x7F) | 0x80)
            self.writeByte(((v >> 7) & 0x7F) | 0x80)
            self.writeByte(v & 0x7F)
        else:
            self.writeByte(((v >> 22) & 0x7F) | 0x80)
            self.writeByte(((v >> 15) & 0x7F) | 0x80)
            self.writeByte(((v >> 8) & 0x7F) | 0x80)
            self.writeByte(v & 0xFF)

    def sendXtMessage(self, _arg_1: int, _arg_2: dict) -> bytes:
        self.buf = bytearray()
        param = _arg_2.get("param")
        if param is None:
            param = {}
            _arg_2["param"] = param

        _local_5 = self.getMsgNo(_arg_2["id"])  # 秘钥
        param[":ext_seq;"] = _local_5

        # 等价 AS: byteData.writeObject(param)
        writer = SendMessage()
        writer.writeObject(param)
        data_bytes = writer.getvalue()

        _local_11 = {}
        _local_11["data"] = self.encrypt_hex(_local_5, data_bytes)
        _arg_2["param"] = _local_11
        # print(_local_11)
        self.resetMsgBuffer(1, 10033, _arg_1)
        self.writeShort(_arg_2["id"])
        self.writeUTF(_arg_2["cmd"])
        self.writeObject(_local_11)
        return self.build_socket_packet(self.getvalue()) # 发送消息
    def sendXtMessageByte(self, _arg_1: str) -> bytes:
        self.buf = bytes.fromhex(_arg_1)
        return self.build_socket_packet(self.getvalue()) # 发送消息
    def getMsgNo(self, _arg_1: int) -> int:
        if _arg_1 not in self.msgNoObj or self.msgNoObj[_arg_1] is None:
            _local_3 = 0
        else:
            _local_3 = self.msgNoObj[_arg_1]

        _local_2 = self.getMyNextSeq(_local_3)
        self.msgNoObj[_arg_1] = _local_2
        return _local_2 
    def getMyNextSeq(self, _arg_1: int) -> int:

        _local_14 = 0
        _local_13 = 0
        _local_12 = 0
        _local_11 = 0
        _local_9  = 0
        _local_10 = 0
        _local_8  = 0
        _local_5  = 0
        _local_7  = 0

        _local_7 = self.userId
        _local_5 = 72
        _local_14 = _local_7
        _local_13 = _arg_1

        if _local_13 != 0:
            _local_12 = self.mod_as3(_local_14, 108)
            _local_11 = ((_local_13 & 0xFFFFFFFF) >> 1) & 0x0FFFFFFE
            _local_12 = (_local_12 + _local_11)
            _local_5 = (_local_12 << 2)
            if _local_12 >= 123216728:
                _local_5 = 816

        # ===== 原 static 逻辑 =====
        if not self.inited:
            self.seed = int(time.time()) # 获取当前时间戳
            self.inited = True
            # print(self.seed)

        _local_14 = self.seed

        if _local_14 == 0:
            _local_14 = 123459876
            self.seed = _local_14

        # ===== 第一次 RNG =====
        _local_12 = (_local_14 // 127773) * -2836
        _local_11 = self.mod_as3(_local_14, 127773) * 16807
        _local_13 = (_local_11 + _local_12)
        _local_14 = (_local_13 + 2147483647) if (_local_13 < 0) else _local_13

        # ===== 第二次 RNG =====
        _local_10 = 123459876
        _local_13 = _local_14 if (_local_14 != 0) else _local_10

        _local_12 = (_local_13 // 127773) * -2836
        _local_11 = self.mod_as3(_local_13, 127773) * 16807
        _local_9 = (_local_11 + _local_12)
        _local_13 = (_local_9 + 2147483647) if (_local_9 < 0) else _local_9

        if _local_13 != 0:
            _local_10 = _local_13

        # ===== 第三次 RNG =====
        _local_12 = (_local_10 // 127773) * -2836
        _local_11 = self.mod_as3(_local_10, 127773) * 16807
        _local_10 = (_local_11 + _local_12)
        _local_9 = (_local_10 + 2147483647) if (_local_10 < 0) else _local_10

        self.seed = _local_9
        # print(_local_9)
        # ===== 位拼接 =====
        _local_12 = (_local_9 & 0x03)
        # print(_local_5)
        _local_12 = (_local_12 | _local_5)

        _local_11 = (_local_13 << 2)
        _local_8  = (_local_14 << 17)
        _local_11 = (_local_11 + _local_8)
        _local_11 = (_local_11 & 0xE0000000)

        _local_12 = (_local_12 | _local_11)
        
        # 模拟 AS3 int 32位
        _local_12 &= 0xFFFFFFFF
        if _local_12 >= 0x80000000:
            _local_12 -= 0x100000000

        return _local_12
    def resetMsgBuffer(self, _arg_1: int, _arg_2: int, _arg_3: int = -1):
        self.writeByte(_arg_1)
        self.writeShort(_arg_2)
        self.writeInt(_arg_3)
    def build_socket_packet(self, payload: bytes):
        #更新包号
        self.packet_num = self.msgseq.next(self.packet_num, self.userId)
        key_bytes = struct.pack(">I", self.packet_num & 0xFFFFFFFF)
        key_len = len(key_bytes)

        encrypted = bytearray()
        for i, b in enumerate(payload):
            encrypted.append(b ^ key_bytes[i % key_len])

        total_len = len(encrypted) + 4

        packet = (
            struct.pack(">I", total_len) +
            struct.pack(">I", self.packet_num & 0xFFFFFFFF) +
            encrypted
        )

        return packet
    def encrypt_hex(self, key: int, data: bytes) -> bytes:
        # hex -> list[int]
        # print(data.hex())
        # === key 处理 ===
        if key != 0:
            key = (key & 0x1FFFFFFC) >> 2

        xor_key = [
            (key >> 22) & 0xFF,
            (key >> 18) & 0xFF,
            (key >> 9) & 0xFF,
            (key >> 2) & 0xFF,
        ]

        # XOR
        out = [b ^ xor_key[self.mod_as3(i, 4)] for i, b in enumerate(data)]

        # 每 4 字节重排
        block_count = len(out) // 4
        for i in range(block_count):
            base = i * 4
            if self.mod_as3(i, 2) == 0:
                out[base], out[base + 2] = out[base + 2], out[base]
            else:
                out[base + 1], out[base + 3] = out[base + 3], out[base + 1]

        # list[int] -> hex
        return bytes(out)

    # ================= 工具 =================
    def getvalue(self):
        return bytes(self.buf)

    def hex(self):
        return self.buf.hex()
    def mod_as3(self, dividend: int, divisor: int) -> int:
        r = dividend % divisor
        if dividend < 0 and r > 0:
            r -= abs(divisor)
        return r

def load_config(path="config.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
def md5_str(s: str) -> str:
    return hashlib.md5(s.encode('utf-8')).hexdigest()

async def run_one_account(acc, mainAccount, url, path, headers, ismainfun = True):
    account = acc["account"]
    password_plain = acc["password"]
    sign = acc["id"]
    

    # HTTP 登录（同步就放线程池）
    client_http = HttpClientAsync(url)
    resp = await client_http.post_form(path, {
        "account": account,
        "password": md5_str(password_plain),
        "logintype": "",
        "wyToken": "",
        "fromurl": "",
        "webSite": "",
        "token": "",
        "cookieId": "",
        "pi": "",
        "sessionId": "",
        "content": ""
    }, headers)

    if resp.get("c") != "ok":
        print(f"[x] 登录失败: {account}")
        return

    sid = resp["sid"]
    # print(resp["zn"])
    # 处理 IP 列表，只保留尾部 :0
    ip_items = [i.strip() for i in resp["svr"].split(";") if i.strip()]
    ip_list = []

    for item in ip_items:
        if item.endswith(":0"):  # 只保留尾部是 :0 的
            parts = item.split(":")
            ip_list.append({'ip': parts[0], 'port': parts[1]})

    # 处理 zone 列表
    zn_items = [i.strip() for i in resp["zn"].split(";") if i.strip()]
    combined = []

    for g in zn_items:
        parts = g.split('/')
        zone_name = parts[0]          
        values = list(map(int, parts[1:]))
        
        # 排除 zone 名称里包含 'test'
        if "test" in zone_name.lower():
            continue
        
        index = values[0]             # 用第一个数字作为索引
        if index < len(ip_list):      # 防止越界
            ip_info = ip_list[index]
            combined.append({
                'zone': zone_name,
                'values': values,
                'ip': ip_info['ip'],
                'port': ip_info['port']
            })

    # 输出结果
    # print(combined)
    one = random.choice(combined)
    # print(one)
    
    zone = one["zone"]
    server_ip = one["ip"]
    server_port = one["port"]

    client = FlashClientAsync(server_ip, server_port)
    await client.connect()

    res = await client.login(zone, account, sid)
    print(f"[√] 登录成功: {account}")

    send = SendMessage()
    send.setmsgseq(sid)
    send.setUserId(res["id"])

    await client.init_user_info(send, res["lastLoginTime"], 1)
    if sign == 0:
        await client.mainAccount(send, 1) # 主账号的操作（自己登陆 不建议用这个登录）
    else:
        if ismainfun:
            await asyncio.sleep(1)
            if sign == 1 or sign == 3: # 1表示没加满亲密度的账号，3表示加满3000亲密度的账号
                await client.intimacy(send, mainAccount, 1)

            await client.alliance_daily(send, 1)
            await client.daily(send, 1)
            await asyncio.sleep(10)
        else:
            if sign == 1:
                await client.sayhello(send, mainAccount, 1)
                await client.enter_main_hut(send, mainAccount, account, 1) # 加亲密度5min一次30（每天2次）
    await client.close()
def get_user_info(path):
    """
    返回 info 文件夹下的完整路径。
    假设 info 文件夹与 exe 同级。
    """
    if getattr(sys, 'frozen', False):
        # exe 打包后，用 exe 所在目录
        base_dir = os.path.dirname(sys.executable)
    else:
        # 本地运行，用脚本目录
        base_dir = os.path.dirname(os.path.abspath(__file__))

    info_dir = os.path.join(base_dir, "info")
    template_path = os.path.join(info_dir, "ex_" + path)
    if os.path.exists(template_path):
        return template_path
    return os.path.join(info_dir, path)
def single_instance():
    """
    确保程序只能运行一个实例。
    返回文件对象，如果 None 说明已有实例运行。
    """
    lock_file_path = os.path.join(os.path.dirname(sys.executable), "program.lock")

    # 打开或创建锁文件
    fp = open(lock_file_path, "w")
    try:
        # 尝试加锁
        msvcrt.locking(fp.fileno(), msvcrt.LK_NBLCK, 1)
        return fp  # 返回锁文件对象，程序退出前保持打开
    except IOError:
        # 锁失败，说明已有实例运行
        return None

# -------------------------
# 测试入口
# -------------------------
async def main():
    config = load_config(get_user_info("config.json"))
    headers = config["default_headers"]
    userinfo = load_config(get_user_info("userInfo.json"))
    accounts = userinfo["accounts"]
    webinfo = load_config(get_user_info("webInfo.json"))
    ismainfun = False # 刷亲密度测试（未完善）
    sametimeloginnumber = 5
    # 限制最多 60 个
    if len(accounts) > 60:
        accounts = accounts[:60]
        print("⚠ 账号超过60个，只取前60个")
    # 筛选 id = 1 的账户
    id_1_accounts = [acc for acc in accounts if acc.get('id') == 1]
    id_1_count = len(id_1_accounts)
    if len(id_1_accounts) > 25:
        print(f"发现 {id_1_count} 个 id=1 的账户，最多只允许出现25个！")
        return
    
    if not ismainfun:
        sametimeloginnumber = 25 # 同时登录账号数
    
    # 并发上限（相当于 max_workers=10）
    sem = asyncio.Semaphore(sametimeloginnumber)

    async def sem_run(acc):
        async with sem:
            await run_one_account(acc, webinfo["mainaccount"], webinfo["url"], webinfo["path"], headers, ismainfun)

    tasks = [asyncio.create_task(sem_run(acc)) for acc in accounts]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    # -------------------------
    # 单实例检测
    # -------------------------
    lock_fp = single_instance()
    if not lock_fp:
        print("程序已经在运行中！")
        sys.exit(0)

    # -------------------------
    # 异步主函数
    # -------------------------
    try:
        asyncio.run(main())
    finally:
        # 程序退出前释放锁
        lock_fp.close()
