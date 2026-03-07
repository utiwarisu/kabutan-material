fetch("material.json")
  .then(r => r.json())
  .then(data => {
    const tbody = document.querySelector("#table tbody");

    data.forEach(d => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${d.code}</td>
        <td>${d.title}</td>
        <td><a href="${d.url}" target="_blank" rel="noopener noreferrer">記事</a></td>
        <td>${d.time}</td>
      `;
      tbody.appendChild(tr);
    });
  })
  .catch(err => {
    const tbody = document.querySelector("#table tbody");
    const tr = document.createElement("tr");
    tr.innerHTML = `<td colspan="4">読み込み失敗: ${err}</td>`;
    tbody.appendChild(tr);
  });
