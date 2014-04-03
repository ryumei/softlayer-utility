softlayer メモ
=================

NAKAJIMA Takaaki



Object Storage
-----------------

アカウント開設直後は、Object Storage は利用できない。
メニューから移動しても何も表示されない。
「Order Object Storage」を選択する必要がある。
(Pay as you go なのでこの時点では、課金は発生しない)

Network billing
-----------------

PayPal のものもある。


ベストプラクティス
----------------------------------------

http://knowledgelayer.softlayer.com/gettingstarted/best-practices

* 最新情報に保つ (Keep Up to Date)

  * 会社情報を最新に保つ
  * 支払い情報を維持する
  
* 安全に保つ (Keep Safe)

  * マスタログイン情報を共有しない
  * 権限に基づいた、もしくはユーザ固有のアカウントを設置する
  * 責任をもってパスワードを管理する
  * セキュアなシステムにする
  * プライベートネットワークを使うこと
  * ファイアウォールをバイパスモードのままにしない
  * RDP, SSH, コントロールポートをそのままにしない
    http://knowledgelayer.softlayer.com/procedure/disable-windows-remote-desktop-rdp-public-network-windows-2003-2008
    http://knowledgelayer.softlayer.com/procedure/restrict-ssh-access-public-network
  * 冗長性を当然と思わない
  * データのバックアップを確認することなく OS 再読み込みを行わない

* 賢く (スマートに) 保つ (Keep Smart)

  * 環境を監視する
  * ネットワークメンテナンスと計画外イベントに通じておくこと
  * SoftLayer Mobile を使う
  * マスタサービスアグリーメント (MSA) を読む
    http://www.softlayer.com/about/legal/standard-msa
  * SoftLayer からのメールをフィルタしたり、無視したりしない

* SoftLayer を運用サイクルの中に参加させる (Keep Us in the Loop)

  * 同じ問題で複数のチケットを切らないで
  * ASM (Adaptec Storage Manager) を削除しないで


/etc/ssh/sshd_config

Listen port を変更
作業用アカウントを作成後、PermitRootLogin を no に。


Result Limit について
-------------------------------

http://sldn.softlayer.com/article/Using-Result-Limits-SoftLayer-API


Object Stroage
--------------------------------

1 オブジェクト当たり 5GB まで。超える場合は、分割して保存することも可能。
名称は、URL エンコードしたときに 1024 文字以下になること。

http://sldn.softlayer.com/article/Introduction-Object-Storage