function isItemInStock() {
  // @todo Pass these in so the same list can be used in non-JS fetchers
  const outOfStockTexts = [
    '0 in stock',
    'agotado',
    'artikel zurzeit vergriffen',
    'available for back order',
    'backordered',
    'brak w magazynie',
    'brak na stanie',
    'coming soon',
    'currently unavailable',
    'en rupture de stock',
    'as soon as stock is available',
    'message if back in stock',
    'nachricht bei',
    'nicht auf lager',
    'nicht lieferbar',
    'nicht zur verfügung',
    'no disponible temporalmente',
    'not available',
    'not in stock',
    'out of stock',
    'out-of-stock',
    'não estamos a aceitar encomendas',
    'produkt niedostępny',
    'no longer in stock',
    'sold out',
    'temporarily out of stock',
    'temporarily unavailable',
    'we do not currently have an estimate of when this product will be back in stock.',
    'zur zeit nicht an lager',
  ];


  const negateOutOfStockRegexs = [
      '[0-9] in stock'
  ]
  var negateOutOfStockRegexs_r = [];
  for (let i = 0; i < negateOutOfStockRegexs.length; i++) {
    negateOutOfStockRegexs_r.push(new RegExp(negateOutOfStockRegexs[0], 'g'));
  }


  const elementsWithZeroChildren = Array.from(document.getElementsByTagName('*')).filter(element => element.children.length === 0);

  // REGEXS THAT REALLY MEAN IT'S IN STOCK
  for (let i = elementsWithZeroChildren.length - 1; i >= 0; i--) {
    const element = elementsWithZeroChildren[i];
    if (element.offsetWidth > 0 || element.offsetHeight > 0 || element.getClientRects().length > 0) {
      var elementText="";
      if (element.tagName.toLowerCase() === "input") {
        elementText = element.value.toLowerCase();
      } else {
        elementText = element.textContent.toLowerCase();
      }

      if (elementText.length) {
        // try which ones could mean its in stock
        for (let i = 0; i < negateOutOfStockRegexs.length; i++) {
          if (negateOutOfStockRegexs_r[i].test(elementText)) {
            return 'Possibly in stock';
          }
        }
      }
    }
  }

  // OTHER STUFF THAT COULD BE THAT IT'S OUT OF STOCK
  for (let i = elementsWithZeroChildren.length - 1; i >= 0; i--) {
    const element = elementsWithZeroChildren[i];
    if (element.offsetWidth > 0 || element.offsetHeight > 0 || element.getClientRects().length > 0) {
      var elementText="";
      if (element.tagName.toLowerCase() === "input") {
        elementText = element.value.toLowerCase();
      } else {
        elementText = element.textContent.toLowerCase();
      }

      if (elementText.length) {
        // and these mean its out of stock
        for (const outOfStockText of outOfStockTexts) {
          if (elementText.includes(outOfStockText)) {
            return elementText; // item is out of stock
          }
        }
      }
    }
  }

  return 'Possibly in stock'; // possibly in stock, cant decide otherwise.
}

// returns the element text that makes it think it's out of stock
return isItemInStock();