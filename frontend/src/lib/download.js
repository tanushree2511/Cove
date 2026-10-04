/** Save a same-origin URL to disk through the browser's normal download mechanism. */
export function downloadUrl(url, filename) {
  const a = document.createElement('a');
  a.href = url;
  a.download = filename || '';
  a.rel = 'noopener';
  document.body.appendChild(a);
  a.click();
  a.remove();
}

/** "…/test_images/IMG_0001.jpg?x=1" -> "IMG_0001.jpg" */
export function filenameOf(pathOrUrl) {
  try {
    return decodeURIComponent(String(pathOrUrl).split('?')[0].split(/[\\/]/).pop());
  } catch {
    return String(pathOrUrl).split('?')[0].split(/[\\/]/).pop();
  }
}
