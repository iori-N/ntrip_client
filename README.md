# ntrip_client

NTRIPサーバからRTCM補正データを受信し、ROS2トピックとして配信するパッケージです。
`ublox_gnss_driver` パッケージと連携して使用することを想定しています。

## 概要

NTRIPサーバにソケット接続し、受信したRTCMデータを `std_msgs/msg/UInt8MultiArray`（生バイト列）として配信します。
また、`ublox_gnss_driver` が配信するGGA文（NMEA）をNTRIPサーバへ送信し、VRS等の補正に対応します。

## 動作環境

- ROS2 (Jazzy等)
- Python 3
- 依存パッケージ: `rclpy`, `std_msgs`

## パッケージ構成

```
ntrip_client/
├── ntrip_client/
│   ├── __init__.py
│   └── ntrip_client_node.py    # メインノード
├── config/
│   └── ntrip_params.yaml       # 接続パラメータ（テンプレート）
├── launch/
│   └── ntrip_client.launch.py  # launchファイル
├── reference/
│   └── ntrip.py                # 参照用の元スクリプト（ROS1）
├── package.xml
├── setup.py
└── setup.cfg
```

## セットアップ

### 1. ビルド

```bash
cd ~/ros2_ws
colcon build --packages-select ntrip_client
source install/setup.bash
```

### 2. パラメータ設定

`config/ntrip_params.yaml` をご利用のNTRIPサービスに合わせて編集してください。

```yaml
ntrip_client_node:
  ros__parameters:
    ntrip_address: "your.ntrip-server.com"   # NTRIPサーバのアドレス
    ntrip_port: 2101                          # ポート番号
    ntrip_username: "your_username"           # ユーザ名
    ntrip_password: "your_password"           # パスワード
    ntrip_mountpoint: "your_mountpoint"       # マウントポイント
```

> **注意**: パスワード等の認証情報を含むため、編集後のYAMLファイルをGitリポジトリにコミットしないよう注意してください。

## 起動方法

### launchファイルで起動（推奨）

```bash
ros2 launch ntrip_client ntrip_client.launch.py
```

`config/ntrip_params.yaml` のパラメータが自動的に読み込まれます。

### ノード単体で起動

パラメータを直接指定して起動することも可能です。

```bash
ros2 run ntrip_client ntrip_client_node --ros-args \
  -p ntrip_address:="your.ntrip-server.com" \
  -p ntrip_port:=2101 \
  -p ntrip_username:="your_username" \
  -p ntrip_password:="your_password" \
  -p ntrip_mountpoint:="your_mountpoint"
```

## トピック

### Subscribe

| トピック名 | 型 | 説明 |
|---|---|---|
| `/gngga` | `std_msgs/msg/String` | `ublox_gnss_driver` が配信するGGA文（NMEA）。NTRIPサーバへの位置情報送信に使用 |

### Publish

| トピック名 | 型 | 説明 |
|---|---|---|
| `/ntrip_rtcm` | `std_msgs/msg/UInt8MultiArray` | NTRIPサーバから受信したRTCMデータ（生バイト列） |

## パラメータ一覧

| パラメータ名 | 型 | デフォルト値 | 説明 |
|---|---|---|---|
| `ntrip_address` | string | `""` | NTRIPサーバアドレス |
| `ntrip_port` | int | `2101` | NTRIPサーバポート番号 |
| `ntrip_username` | string | `""` | 認証ユーザ名 |
| `ntrip_password` | string | `""` | 認証パスワード |
| `ntrip_mountpoint` | string | `""` | マウントポイント名 |

## ublox_gnss_driver との連携

本パッケージは以下のデータフローで `ublox_gnss_driver` と連携します。

```
ublox_gnss_driver                    ntrip_client                    NTRIPサーバ
      |                                   |                              |
      |--- /gngga (String) ------------->|                              |
      |                                   |--- GGA送信 ---------------->|
      |                                   |<-- RTCMデータ受信 ----------|
      |<-- /ntrip_rtcm (UInt8MultiArray) -|                              |
      |                                   |                              |
```

1. `ublox_gnss_driver` がGNSSレシーバからGGA文を取得し `/gngga` トピックに配信
2. `ntrip_client` がGGA文を受信し、NTRIPサーバへ送信（VRS基準局の選択に使用）
3. NTRIPサーバからRTCM補正データを受信
4. RTCMデータを `/ntrip_rtcm` トピックに `UInt8MultiArray`（生バイト列）として配信
5. `ublox_gnss_driver` がRTCMデータを受信し、GNSSレシーバへ転送してRTK測位を実行

## エラーハンドリング

- NTRIPサーバへの接続失敗時は、5秒間隔で自動的に再接続を試みます
- ソケット通信中のエラー（切断含む）を検知すると、自動的に再接続します
- 各種エラーはROS2ログに出力されます

## トラブルシューティング

### 接続できない場合

- パラメータ（アドレス、ポート、ユーザ名、パスワード、マウントポイント）が正しいか確認してください
- ファイアウォールでNTRIPサーバへの通信がブロックされていないか確認してください
- ログを確認してエラーメッセージを確認してください:
  ```bash
  ros2 launch ntrip_client ntrip_client.launch.py
  ```

### `/ntrip_rtcm` にデータが配信されない場合

- NTRIPサーバへの接続が成功しているかログを確認してください
- `/gngga` トピックにGGAデータが配信されているか確認してください:
  ```bash
  ros2 topic echo /gngga
  ```

### マウントポイントエラー

ログに `Invalid or no mountpoint` と表示される場合、指定したマウントポイント名が正しいか確認してください。
