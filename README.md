###### tags: `つくばロボットコンテスト2021` `Tsukuba Univ`
# Documentation of Raspberry Pi Control Program

## GitHubリポジトリ
[GitHub - robocon-11/robocon-11-raspi](https://github.com/robocon-11/robocon-11-raspi)

## 用語の解説
- **Raspberry Pi**：このプログラムの実行に用いるコンピュータの名前
- **シリアル通信**：バス（通信経路）上を一度に1ビットずつ、逐次的にデータを送ることをいう。（[Wikipedia](https://ja.wikipedia.org/wiki/%E3%82%B7%E3%83%AA%E3%82%A2%E3%83%AB%E9%80%9A%E4%BF%A1)より）ここでは特に、USBを用いたシリアル通信のことを指す。
- **UDP通信**：インターネットなどで使用される通信プロトコルであり、インターネット・プロトコル・スイートのうち、トランスポート層のプロトコルの一つ。（[Wikipedia](https://ja.wikipedia.org/wiki/User_Datagram_Protocol)より）
- **パケット**：制御プログラム（このプログラム）とやり取りするために受け渡すデータのこと。実機ではArduinoとシリアル通信を用いてパケットを介することでデータの入出力を行う。
- **シリアライズ**：Pythonオブジェクトとして表現されたパケットを、byte配列に変換する操作のこと。
- **デシリアライズ**：シリアライズとは逆に、byte配列で表されたパケットをPythonオブジェクトに変換する操作のこと。

## このプログラムの役割
- 自律走行に特化したプログラムであり、センサ等から入力された値をもとに走行するための指示を出力する。（いわゆる自律走行アルゴリズムのサーバー的役割を果たす。）
- よって一部を除いて、各センサやアクチュエータ類を制御するという低レイヤの実装は行っていない。
- この実装を行うことにより、本プログラムの出力するパケットとそれらに対応する入力パケットの処理の実装ができれば、出力先を問わず汎用的にロボットを制御することが可能である。（本プログラムには入出力先としてシリアル通信とUDP通信の二種類が定義されており、本プログラムをベースとしたロボットの遠隔制御も可能である。）

## GPIOの接続
[このページ](https://hackmd.io/@itsu-dev/Hk-TIg94K)を参照していただきたい。

## システムの概略図
### センサの計測と読み取り
![](https://i.imgur.com/HJDDDsa.png)


### アクチュエータの動作
![](https://i.imgur.com/ESFrKLw.png)

## 各クラス・ファイルの概要
各クラスとファイル、およびそれらで定義されている関数に関する詳細な説明については[GitHub](https://github.com/robocon-11/robocon-11-raspi/tree/master/robot_controller)を参照してほしい。

- ***robot_controller***
    - **Core ([core.py](https://github.com/robocon-11/robocon-11-raspi/blob/master/robot_controller/core.py))**
        - ロボットの自律走行の核となるアルゴリズムを記述している。メインクラスとしても機能している。
    - **[led_indicator.py](https://github.com/robocon-11/robocon-11-raspi/blob/master/robot_controller/led_indicator.py)**
        - コントローラ基盤のLEDの表示を制御する。
    - **[robot_manager.py](https://github.com/robocon-11/robocon-11-raspi/blob/master/robot_controller/robot_manager.py)**
        - ロボットのモーターの制御する。（前進、後進、旋回）
    - ***sensor***
        - **SensorManager([sensor_manager.py](https://github.com/robocon-11/robocon-11-raspi/blob/master/robot_controller/sensor/sensor_mamager.py))**
            - センサ計測用のパケットおよびコールバック用関数を保持する。
    - ***connection***
        - **InputPacket ([input_packets.py](https://github.com/robocon-11/robocon-11-raspi/blob/master/robot_controller/connection/input_packets.py))**
            - 入力されるパケット群の実装。
            - [実装済みのパケット一覧](https://hackmd.io/368MXmhcQKylxj9JzOH0ag)
                - RightSteppingMotorAlertPacket *implements InputPacket*
                - RightSteppingMotorFeedbackPacket *implements InputPacket*
                - LeftSteppingMotorAlertPacket *implements InputPacket*
                - LeftSteppingMotorFeedbackPacket *implements InputPacket*
                - BothSteppingMotorAlertPacket *implements InputPacket*
                - BothSteppingMotorFeedbackPacket *implements InputPacket*
                - DistanceSensorResultPacket *implements InputPacket*
                - LineTracerResultPacket *implements InputPacket*
                - UpperServoMotorFeedbackPacket *implements InputPacket*
                - BottomServoMotorFeedbackPacket *implements InputPacket*
                - NineAxisSensorResultPacket *implements InputPacket*
        - **OutputPacket ([output_packets.py](https://github.com/robocon-11/robocon-11-raspi/blob/master/robot_controller/connection/output_packets.py))**
            - 出力するパケット群の実装。
            - [実装済みのパケット一覧](https://hackmd.io/368MXmhcQKylxj9JzOH0ag)
                - RightSteppingMotorPacket *implements OutputPacket*
                - LeftSteppingMotorPacket *implements OutputPacket*
                - BothSteppingMotorPacket *implements OutputPacket*
                - MeasureDistanceToBallPacket *implements OutputPacket*
                - MeasureLineTracerPacket *implements OutputPacket*
                - UpperServoMotorPacket *implements OutputPacket*
                - BottomServoMotorPacket *implements OutputPacket*
                - MeasureNineAxisSensorPacket *implements OutputPacket*
        - **[connection_manager.py](https://github.com/robocon-11/robocon-11-raspi/blob/master/robot_controller/connection/connection_manager.py)**
            - パケットをシリアライズし、各インターフェースとの入出力を制御する。
            - パケットのキューイング
        - **PacketEventListener ([packet_event_listener.py](https://github.com/robocon-11/robocon-11-raspi/blob/master/robot_controller/connection/packet_event_listener.py))**
            - 入力パケットをもとに、それに対応するSensorManagerを起動する。
        - ***interface***
            - **ConnectionInterface ([connection_interface.py](https://github.com/robocon-11/robocon-11-raspi/blob/master/robot_controller/connection/interface/connection_interface.py))**
                - 入出力インターフェースのためのインターフェース。
                - 実際の入出力インターフェースはこのクラスを実装する。
            - **NetworkInterface ([network_interface.py](https://github.com/robocon-11/robocon-11-raspi/blob/master/robot_controller/connection/interface/network_interface.py))** *implements ConnectionInterface*
                - UDP通信を介した入出力インターフェースの実装。
            - **SerialInterface ([serial_interface.py](https://github.com/robocon-11/robocon-11-raspi/blob/master/robot_controller/connection/interface/serial_interface.py)** *implements ConnectionInterface*
                - シリアル通信を介した入出力インターフェースの実装。

## 各パケットの実装
[このページ](https://hackmd.io/@itsu-dev/BkVAQk_Rd)を参照していただきたい。

## 制御の仕組み
### 制御アルゴリズム
執筆中

### 通信制御
#### インターフェースを用いた通信
>インターフェースとは、接点、境界面、接触面、接合面、仲立ち、橋渡しなどの意味を持つ英単語。IT関連では、二つのものが接続・接触する箇所や、両者の間で情報や信号などをやりとりするための手順や規約を定めたものを意味する。

（[e-Words](https://e-words.jp/w/%E3%82%A4%E3%83%B3%E3%82%BF%E3%83%BC%E3%83%95%E3%82%A7%E3%83%BC%E3%82%B9.html)より引用）

制御ソフトウェアをデバッグする際、Arduinoや実機の開発が終わっていなかったが、どうにかして行う必要があった。そこで通信部分をArduinoのシリアル通信用に限定して書くよりも、通信が可能な方法全てに対して実装が可能なように、より抽象化して書いたほうが良いとの結論に至った。

通信が可能な方法全てとは、例えば以下のようなものが挙げられる。
- シリアル通信（USB）
- UDP通信（インターネットを介した通信手法）
- Bluetooth通信

このうち上二つについては、本プログラムに実装されている。このように実装することで、クライアントとなるソフトを何らかの方法で実装することができれば、ロボット自体ももちろん、ロボットの動作をエミュレート（模倣）することも可能になる。

さらに、これらのインターフェースを同時に接続することも（実装次第では）可能なため、例えば低レイヤ部の制御にArduinoを2台用いるということも可能である。

#### キューイング
>キューとは、最も基本的なデータ構造の一つで、要素を入ってきた順に一列に並べ、先に入れた要素から順に取り出すという規則で出し入れを行うもの。順番を待つ人の行列と同じ仕組みであるため「待ち行列」とも訳される。

（[e-Words](https://e-words.jp/w/%E3%82%AD%E3%83%A5%E3%83%BC.html)より引用）

各インターフェースを通して通信する際、通信相手にひとつ前に送られてきたパケットの処理が終わってないまま次のパケットを送ってしまうと、何らかの問題が起こる可能性がある。

これを解決するために「キューイング」を実装した。キューイングを用いるとパケットの通信制御がより安全になる。この仕組みは以下のとおりである。

0. （常時）Raspberry Piは常にキューを10msごとに別スレッドで監視し、キューにパケットがあればそれを取り出して送信する。
1. （送信時）Raspberry Piで送信するパケットをキュー（リスト）に登録する
2. （受信時）"Stop"の文字列が返ってきた場合、送信を一時停止する。
3. （受信時）送信したパケットのランダムなIDが返ってきた場合、受信が完了したとみなして送信を再開する。

### センサの測定
#### センサ測定の非同期処理の実装
センサで何かの値を測定するとき、Raspberry Pi自体ではセンサの測定をしていないため、欲しいタイミングですぐにその値が得られるわけではない。つまり、センサ測定時に値が得られるまでにタイムラグが発生してしまうという問題がある。

そこで、高階関数を用いたコールバック機構と入出力パケットにランダムなIDを載せることで、この問題を解決した。

- **高階関数**
>高階関数とは、第一級関数をサポートしているプログラミング言語において少なくとも以下のうち1つを満たす関数である
　・ 関数（手続き）を引数に取る
　・ 関数を返す

（[Wikipedia](https://ja.wikipedia.org/wiki/%E9%AB%98%E9%9A%8E%E9%96%A2%E6%95%B0)より引用）
いわゆる「関数自体を値にしてしまう」ことである。

- **コールバック**
>コールバックとは、コンピュータプログラム中で、ある関数などを呼び出す際に別の関数などを途中で実行するよう指定する手法のこと。呼び出し側の用意した関数などを、呼び出し先のコードが「呼び出し返す」（callback）ように登録する。

（[e-Words](https://e-words.jp/w/%E3%82%B3%E3%83%BC%E3%83%AB%E3%83%90%E3%83%83%E3%82%AF.html)より引用）
いわゆる「突然何かが起きたとき、あらかじめ指定しておいた関数を呼び出す」ことである。

つまり、ランダムなIDを載せたセンサ測定指示パケットを生成するときに、高階関数としてコールバック用の関数を指定しておき、そのパケットを送信する。そして、その指示の応答として帰ってきたパケットに最初指定したIDが載っていれば、あらかじめ指定しておいたコールバック用の関数を呼び出してやる、といった具合である。

#### ライントレーサの実装
本プログラムでは、床にあるラインを検出するライントレーサとしてフォトトランジスタを使用する。この値を読み取る際にも上記の問題が発生してしまうため、以下の処理方法にて実装を行った。

0. 測定用のスレッドを立ち上げ、1,000msおき（今後の状況によっては間隔が変わる場合もある）にループを行う。
1. ループの中でSensorManagerを介してMeasureLineTracerPacketを送る。
2. LineTracerResultPacketを受信したら、フィードバックとしてコールバック関数を呼び出す。

#### 測距センサの実装
本プログラムでは、前方にある壁との距離を測定するために超音波センサを使用する。この値を読み取る際にも上記の問題が発生してしまうため、以下の処理方法にて実装を行った。

0. 測定用のスレッドを立ち上げ、1,000msおき（今後の状況によっては間隔が変わる場合もある）にループを行う。
1. ループの中でSensorManagerを介してMeasureDistancePeacketを送る。
2. DistanceSensorResultPacketを受信したら、フィードバックとしてコールバック関数を呼び出す。

## エミュレーション
このプログラムを開発中、特に自律走行のアルゴリズムを書くために、デバッグが必要になった。そこで、実機はまだ完成していなかったためMinecraft上でのデバッグを試みた。専用のクライアントプログラムを開発し、それをMinecraftサーバー用のプラグインとして実装することで実現した。

### デバッグ環境の構築
#### 前提
- Javaが実行できる環境が構築されている
- Gitがインストールされている
- Mavenを用いたビルドができる
- Minecraft（統合版）が使用できる

#### 1. 専用フォルダの作成
デスクトップに```nukkit```フォルダを作成する。

#### 2. Cloudburst Nukkitのダウンロード
[このページ](https://ci.opencollab.dev/job/NukkitX/job/Nukkit/job/master/)から「nukkit-1.0-SNAPSHOT.jar」をダウンロードし、先ほど作成した```nukkit```フォルダに配置する。

#### 3. 実行スクリプトの作成
nukkitフォルダ内に「start.cmd（Linuxならstart.sh）」というファイルを作成し、以下のコードを記述する。
```shell=
java -jar nukkit-1.0-SNAPSHOT.jar
```

#### 4. スクリプトを実行する
先ほど作成したファイルをダブルクリック等で実行する。

#### 5. エミュレータソフトをクローンする
nukkitフォルダ内に```emulator```フォルダを作り、以下のコマンドを実行して[GitHubリポジトリ](https://github.com/robocon-11/robocon-11-robot-emulator)をクローンする。
```shell=
git clone https://github.com/robocon-11/robocon-11-robot-emulator
```

#### 6. ビルドする
```emulator```フォルダに遷移し、以下のコマンドを実行する。
```shell=
mvn package
```

#### 7. ファイルを配置する
```emulator/target```内に```mainModule-1.0-SNAPSHOT-jar-with-dependencies.jar```が生成されるので、これをコピーして```nukkit/plugins```内に貼り付ける。

### 実行
start.cmdをダブルクリック等で実行し、Minecraftのサーバーを起動させる。

### エミュレーションを実行
#### 1. 外部サーバーの追加をする
Minecraftを起動し、「外部サーバーの追加」から「アドレス」にPCのIPアドレス、「ポート」に19132をそれぞれ入力する。

#### 2. サーバーに入る
先ほど追加したサーバーを選択し、参加する。

#### 3. (7, 7, 7)に移動する
```/tp 7 7 7```を実行し、座標(7, 7, 7)に移動する。
