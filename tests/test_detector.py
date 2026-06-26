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

    assert detect_stock_status(html) == StockStatus.UNKNOWN


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
    assert detect_stock_status("<button>Sepete ekle</button>", has_visible_add_to_cart=True) == StockStatus.IN_STOCK


def test_add_to_basket_wins_over_variant_out_of_stock_text() -> None:
    html = """
    <main>
      <h1>Altin dugmeli ceket</h1>
      <button>Sepete ekle</button>
      <span>XS stokta yok</span>
    </main>
    """

    assert detect_stock_status(html, has_visible_add_to_cart=True) == StockStatus.IN_STOCK


def test_schema_in_stock_does_not_win_over_visible_sold_out_text() -> None:
    html = """
    <html>
      <head>
        <script type="application/ld+json">
          {"@type": "Product", "offers": {"availability": "https://schema.org/InStock"}}
        </script>
      </head>
      <body>Tükendi</body>
    </html>
    """

    assert detect_stock_status(html) == StockStatus.OUT_OF_STOCK


def test_related_products_sold_out_does_not_create_out_of_stock_status() -> None:
    html = """
    <main>
      <h1>Z1975 Kisa Dantel Denim Ceket</h1>
      <button>Sepete ekle</button>
      <section>Benzer ürünler Tükendi</section>
    </main>
    """

    assert detect_stock_status(html) == StockStatus.UNKNOWN


def test_related_products_sold_out_does_not_override_visible_product_add_to_basket() -> None:
    html = """
    <main>
      <h1>Z1975 Kisa Dantel Denim Ceket</h1>
      <button>Sepete ekle</button>
      <section>Benzer ürünler Tükendi</section>
    </main>
    """

    assert detect_stock_status(html, has_visible_add_to_cart=True) == StockStatus.IN_STOCK


def test_product_sold_out_wins_over_static_add_to_basket_text() -> None:
    html = """
    <main>
      <h1>Z1975 Kisa Dantel Denim Ceket</h1>
      <button>Sepete ekle</button>
      <p>Tükendi</p>
    </main>
    """

    assert detect_stock_status(html) == StockStatus.OUT_OF_STOCK


def test_product_sold_out_wins_over_visible_add_to_basket_signal() -> None:
    html = """
    <main>
      <h1>Z1975 Kisa Dantel Denim Ceket</h1>
      <button>Sepete ekle</button>
      <p>Tükendi</p>
    </main>
    """

    assert detect_stock_status(html, has_visible_add_to_cart=True) == StockStatus.OUT_OF_STOCK


def test_extracts_open_graph_title() -> None:
    html = '<meta property="og:title" content="Keten Gomlek | ZARA Turkiye">'

    assert extract_title(html) == "Keten Gomlek | ZARA Turkiye"
