import React from 'react';

export function MarketRatings({ ratings = {}, onChange }) {
  return (
    <fieldset className="market-ratings">
      <legend>Lab-reported nutrient ratings</legend>
      <p className="muted">Copy the ratings from the report. These determine the product ranking.</p>
      <div className="fields three">
        {['n', 'p', 'k'].map(nutrient => (
          <label key={nutrient}>{nutrient.toUpperCase()} rating
            <select value={ratings[nutrient] || ''} onChange={event =>
              onChange({ ...ratings, [nutrient]: event.target.value })
            }>
              <option value="">Unknown</option>
              <option value="low">Low</option>
              <option value="adequate">Adequate</option>
              <option value="high">High</option>
            </select>
          </label>
        ))}
      </div>
    </fieldset>
  );
}

export function MarketResults({ report }) {
  if (!report.market_note) return null;
  return (
    <section className="panel">
      <h3>Ranked Indian market fertilizers</h3>
      <p>{report.market_note}</p>
      <p><a href="https://iffcobazar.co.in/en/products" target="_blank" rel="noreferrer">IFFCO online catalog</a>
        {' · '}<a href="https://www.coromandel.biz/products-services/fertiliser-2/" target="_blank" rel="noreferrer">Coromandel catalog</a>
        {' · '}Offline, ask a licensed agri-input dealer for the exact grade on the bag.
        Confirm local stock, delivery to your PIN code and current prices with the seller.
      </p>
      <div className="market-grid">
        {report.market_products.map(product => (
          <article className="panel" key={product.name}>
            <span className="eyebrow">RANK {product.rank}</span>
            <h4>{product.name} · {product.grade}</h4>
            <p><b>Matches low ratings:</b> {product.covers.join(', ')}.
              {product.extra.length > 0 && <> Also adds {product.extra.join(', ')}.</>}
            </p>
            <p><b>Pros:</b> {product.pros}</p>
            <p><b>Cons:</b> {product.cons}</p>
          </article>
        ))}
      </div>
      <p className="disclaimer">Rank is an indicative nutrient match. Confirm the grade, quantity and timing with local crop guidance before buying or applying.</p>
    </section>
  );
}
