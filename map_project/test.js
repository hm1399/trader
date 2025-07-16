
fetch('svg_map.json')
  .then(response => response.json())
  .then(data => {
    console.log(data.id);
    console.log(data.xmlns);
    console.log(data.viewBox);
    console.log(data['aria-label']);
  })
  .catch(error => console.error('Error loading JSON:', error));