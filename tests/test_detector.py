from zarabot.detector import StockStatus, detect_stock_status, extract_title


def test_detects_schema_in_stock() -> None:
    html = """
    <html>
      <head>
        <script type="application/ld+json">
          {"@type": "Product", "offers": {"availability": "https://schema.org/InStock"}}
        </script>
      </head>
    </html>
    """

    assert detect_stock_status(html) == StockStatus.IN_STOCK


def test_detects_schema_out_of_stock() -> None:
    html = """
    <html>
      <head>
        <script type="application/ld+json">
          {"@type": "Product", "offers": [{"availability": "https://schema.org/OutOfStock"}]}
        </script>
      </head>
    </html>
    """

    assert detect_stock_status(html) == StockStatus.OUT_OF_STOCK


def test_detects_turkish_out_of_stock_text() -> None:
    assert detect_stock_status("<main>Bu beden stokta yok</main>") == StockStatus.OUT_OF_STOCK


def test_detects_turkish_add_to_basket_text() -> None:
    assert detect_stock_status("<button>Sepete ekle</button>") == StockStatus.IN_STOCK


def test_add_to_basket_wins_over_variant_out_of_stock_text() -> None:
    html = """
    <main>
      <h1>Altin dugmeli ceket</h1>
      <button>Sepete ekle</button>
      <span>XS stokta yok</span>
    </main>
    """

    assert detect_stock_status(html) == StockStatus.IN_STOCK


def test_extracts_open_graph_title() -> None:
    html = '<meta property="og:title" content="Keten Gomlek | ZARA Turkiye">'

    assert extract_title(html) == "Keten Gomlek | ZARA Turkiye"
