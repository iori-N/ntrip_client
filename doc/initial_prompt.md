# NTRIP Client ROS2パッケージの作成

## 概要
既存のROS1スクリプトを参照し、同等の機能を持つROS2パッケージを作成してください。
パッケージ名は `ntrip_client` とします。

## 参照スクリプト（ROS1）
- `ros2_ws/src/ntrip_client/reference/ntrip.py`

## 重要: 連携パッケージとの整合性
本パッケージは `ublox_gnss_driver` パッケージと連携する。
`ublox_gnss_driver` 側では RTCMトピックを `std_msgs/msg/UInt8MultiArray` として
Subscribeしている。必ずこの型に合わせること。

## 機能

### ntrip_client_node
- NTRIPサーバにソケット接続し、RTCMデータを受信する
- 受信したRTCMデータを `std_msgs/msg/UInt8MultiArray`（生バイト列）として
  `/ntrip_rtcm` トピックに配信する
  - 元スクリプトのhexエンコード方式は使わない。バイナリをそのままUInt8MultiArrayに格納する
- `ublox_gnss_driver` パッケージが配信する `/gngga` トピック（std_msgs/String）をSubscribeし、
  NTRIPサーバへのGGA送信に使用する
- NTRIP接続パラメータはYAMLファイルから読み込む

## 技術要件

### ビルドシステム
- ament_python
- 依存パッケージ: rclpy, std_msgs

### ROS2パラメータ（YAMLファイルで管理）
- `ntrip_address`: NTRIPサーバアドレス
- `ntrip_port`: ポート番号
- `ntrip_username`: ユーザ名
- `ntrip_password`: パスワード
- `ntrip_mountpoint`: マウントポイント

### コード品質
参照スクリプトの以下の問題点を改善すること：
- `while rospy.is_shutdown()` の条件が逆（バグ）→ 正しい起動待機処理にする
- ヘッダ文字列の `"Host \r\n".format(...)` でformat引数が使われていない → 修正
- `self.gngga` の存在チェックが try/except による AttributeError 頼み → 適切な初期化とチェック
- socket通信のエラーハンドリングが不十分 → 接続断時の再接続ロジックを追加
- Python 3対応（encode/decode処理の見直し）
- rclpy.Node を継承したクラス設計
- 適切なロギング（self.get_logger()）
- ソケット受信のブロッキングとROS2スピンの共存（スレッド使用を検討）

### パッケージ構成
```
ntrip_client/
├── ntrip_client/
│   ├── __init__.py
│   └── ntrip_client_node.py
├── config/
│   └── ntrip_params.yaml       # 接続パラメータのテンプレート
├── launch/
│   └── ntrip_client.launch.py
├── reference/                   # 参照用の元スクリプト
│   └── ntrip.py
├── package.xml
├── setup.py
├── setup.cfg
└── README.md
```

### config/ntrip_params.yaml（テンプレート）
パスワード等はダミー値とし、ユーザが書き換える前提のテンプレートとして作成する。

### launchファイル
- ntrip_client_node を起動
- config/ntrip_params.yaml をパラメータファイルとして読み込む

### トピックインターフェース
- Subscribe: `/gngga` (std_msgs/String) — ublox_gnss_driverから
- Publish: `/ntrip_rtcm` (std_msgs/msg/UInt8MultiArray, 生バイト列) — ublox_gnss_driverへ

## 作業手順
1. 参照スクリプトの処理内容を把握する
2. ノードを実装する（エラーハンドリング・再接続ロジック含む）
3. パラメータYAMLテンプレートを作成する
4. launchファイルを作成する
5. package.xml, setup.py を整備する
6. ビルドが通ることを確認する（colcon build）
