# prepare_tool

> フォントのサブセット化とパッケージ化をするツール

## Install

```
docker pull openfonts-jp/prepare-tool
```

もしくは

```
whalebrew install openfonts-jp/prepare-tool
```

## Usage

https://github.com/openfonts-jp/packages の JSON ファイルからパッケージを作ります

```
prepare_tool --output-dir ./output ./files/any-font.json
```

`./fonts` に `.tar.gz` でまとめたファイルが，`./webfonts` にサブセット化したウェブフォントが生成されます

サブセットは JISX0208/0213 にある文字をいくつかのブロックに分けて抽出します

### WOFF extended metadata

このツールでは， [WOFF extended metadata] にライセンスを埋め込みます

そのため，ライセンスを添付して頒布する必要のあるフォントでもウェブフォントとして利用できます

[WOFF extended metadata]: https://www.w3.org/TR/2012/REC-WOFF-20121213/#Metadata

## Contribute

PRs accepted.

## License

MIT (c) 3846masa
