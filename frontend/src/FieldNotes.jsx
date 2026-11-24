import React, { useRef, useState } from 'react';

export function explainMatch(crop, field) {
  const checks = [
    ['soil type', crop.soil.includes(field.soil_type)],
    ['pH', field.ph >= crop.ph[0] && field.ph <= crop.ph[1]],
    ['annual rainfall', field.rainfall >= crop.rain[0] && field.rainfall <= crop.rain[1]],
    ['season', crop.seasons.includes(field.season)],
    ['water availability', crop.water === field.water],
  ];
  const names = value => checks.filter(([, match]) => match === value).map(([label]) => label).join(', ');
  return [names(true) && 'Matches: ' + names(true), names(false) && 'Check locally: ' + names(false)].filter(Boolean).join('. ');
}

export function cropRank(results, score) {
  const rank = results.findIndex(crop => crop.score === score) + 1;
  return results.filter(crop => crop.score === score).length > 1 ? '= ' + rank : rank;
}

export function CropPhoto({ photo, onChange }) {
  const [error, setError] = useState('');
  const version = useRef(0);
  async function select(event) {
    const file = event.target.files[0];
    const current = ++version.current;
    onChange('');
    setError('');
    if (!file) return;
    try {
      if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type) || file.size > 10 * 1024 * 1024) {
        throw new Error('Choose a JPG, PNG or WebP photo under 10 MB.');
      }
      const bitmap = await createImageBitmap(file);
      const scale = Math.min(1, 700 / Math.max(bitmap.width, bitmap.height));
      const canvas = document.createElement('canvas');
      canvas.width = Math.max(1, Math.round(bitmap.width * scale));
      canvas.height = Math.max(1, Math.round(bitmap.height * scale));
      canvas.getContext('2d').drawImage(bitmap, 0, 0, canvas.width, canvas.height);
      bitmap.close();
      if (current === version.current) onChange(canvas.toDataURL('image/jpeg', 0.7));
    } catch (err) {
      if (current === version.current) setError(err.message || 'Choose another photo.');
    }
  }
  return <div><label>Optional crop photo<input type="file" accept="image/jpeg,image/png,image/webp" onChange={select}/></label>
    {photo && <img src={photo} width="150" alt="Selected crop observation"/>}
    {error && <p role="alert">{error}</p>}
    <small>Stored with your diary observation on this device. Lab ratings determine fertilizer ranks.</small></div>;
}
