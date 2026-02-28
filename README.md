# 奥奇传说页游-HELPER
奥奇传说多进程helper，抛弃flash网页操作，直接通过网络层发送命令，给服务器发送socket数据包，从而模拟按钮操作等~

## 优势：
操作流畅、可同时模拟登录多个账号（建议5个为一组同时登陆）

## 缺点：
稳定性未知、封号的可能性未知！

***

下面展示的是59个小号组成的联盟：

![image](https://github.com/YuZi-isNOOB/aqcs-helper/blob/main/img/%E5%B1%8F%E5%B9%95%E6%88%AA%E5%9B%BE%202026-02-25%20003157.png)

## 功能：
- [x] [联盟每日任务](#联盟每日任务)
- [ ] 联盟捐献无敌星元
- [x] [联盟每周领取钻石](#联盟每周领取钻石)
- [x] [每日签到领钻石](#每日签到领钻石)
- [x] [领取每日任务钻石](#领取每日任务钻石)
- [x] [元宝兑换钻石](#元宝兑换钻石)
- [x] [资源秘境领取金币](#资源秘境领取金币)
- [x] [每周亲密好友赠送](#每周亲密好友赠送)
- [ ] [每周亲密好友赠送-无敌星元](#每周亲密好友赠送-无敌星元)
- [x] [亲密度-打招呼](#亲密度-打招呼)
- [ ] 亲密度-同场景5min
- [ ] [粉丝团赠送钻石（暂时不会实现此功能）](#粉丝团赠送钻石)

## 控制台输出演示：

![image](https://github.com/YuZi-isNOOB/aqcs-helper/blob/main/img/%E5%B1%8F%E5%B9%95%E6%88%AA%E5%9B%BE%202026-02-25%20182151.png)

## 联盟每日任务

60人联盟，资金足够支付每周消耗

![image](https://github.com/YuZi-isNOOB/aqcs-helper/blob/main/img/%E5%B1%8F%E5%B9%95%E6%88%AA%E5%9B%BE%202026-02-25%20190357.png)

## 联盟每周领取钻石

每周自动领取5钻石

![image](https://github.com/YuZi-isNOOB/aqcs-helper/blob/main/img/%E5%B1%8F%E5%B9%95%E6%88%AA%E5%9B%BE%202026-02-25%20190604.png)

## 每日签到领钻石

领取每日签到1钻石

![image](https://github.com/YuZi-isNOOB/aqcs-helper/blob/main/img/%E5%B1%8F%E5%B9%95%E6%88%AA%E5%9B%BE%202026-02-25%20190324.png)

## 领取每日任务钻石

自动完成日常任务，领取共3钻石

![image](https://github.com/YuZi-isNOOB/aqcs-helper/blob/main/img/%E5%B1%8F%E5%B9%95%E6%88%AA%E5%9B%BE%202026-02-25%20190335.png)

## 元宝兑换钻石

每攒满100元宝兑换10钻石，每周2次

![image](https://github.com/YuZi-isNOOB/aqcs-helper/blob/main/img/%E5%B1%8F%E5%B9%95%E6%88%AA%E5%9B%BE%202026-02-25%20190635.png)

## 资源秘境领取金币

资源秘境领取金币，为了完成友情商店捐赠

![image](https://github.com/YuZi-isNOOB/aqcs-helper/blob/main/img/%E5%B1%8F%E5%B9%95%E6%88%AA%E5%9B%BE%202026-02-25%20190428.png)

## 每周亲密好友赠送

需要花费金币5k，资源秘境每周溢出

![image](https://github.com/YuZi-isNOOB/aqcs-helper/blob/main/img/%E5%B1%8F%E5%B9%95%E6%88%AA%E5%9B%BE%202026-02-25%20190501.png)

## 每周亲密好友赠送-无敌星元

暂时未完成，需要好友亲密度达到3000！

![image](https://github.com/YuZi-isNOOB/aqcs-helper/blob/main/img/%E5%B1%8F%E5%B9%95%E6%88%AA%E5%9B%BE%202026-02-25%20190508.png)

## 亲密度-打招呼

每次加20亲密度，每天双方互相打招呼都可加一次（每日共40点）

![image](https://github.com/YuZi-isNOOB/aqcs-helper/blob/main/img/%E5%B1%8F%E5%B9%95%E6%88%AA%E5%9B%BE%202026-02-25%20195505.png)

## 粉丝团赠送钻石

### 暂时不会更新这部分，由于60人联盟需要60小号养1个vip大号，而粉丝团还需要4~5个小号，多出来的号只能再创建一个联盟，如果要养的号不是VIP，小号恰好够（vip亲密好友→25，普通账号亲密好友→20 其中多出来的4个小号可以安排在粉丝团）
关于如何60个号养1个号[了解更多](#60养1计算方式)

![image](https://github.com/YuZi-isNOOB/aqcs-helper/blob/main/img/%E5%B1%8F%E5%B9%95%E6%88%AA%E5%9B%BE%202026-02-25%20195714.png)

## 60养1计算方式

1个大号（vip）加25个亲密好友，大号每周领取5×7=35次，每个小号每周产出1个，多出来的一个人没办法，创建一个联盟或者加入一个联盟.

## 如何配置

```id = 1```：附属于大号的 小号 标识，最大25人.

```id = 2```：为联盟赠送星元-小号A 的标识（并且附属于小号B）.

```id = 3```：附属于小号A的 小号 标识，最大19人.

```id = 4```：为联盟赠送星元-小号B 的标识（并且附属于小号A）.

```id = 5```：附属于小号B的 小号 标识，最大14人.

以上组成60人小号团队

```ruby
{
    "account": "xxx",   # 你的小号的账号
    "password": "xxx",  # 你的小号的密码
    "id": 1             # 账号标识
}
```


![License](https://img.shields.io/badge/license-MIT-brightgreen)


