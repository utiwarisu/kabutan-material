fetch("material.json")
  .then(r => r.json())
  .then(data => {
    const tbody = document.querySelector("#table tbody");
    tbody.innerHTML = "";

    data.forEach(d => {
      const tr = document.createElement("tr");

      const m1 = d.materials?.[0] || {};
      const m2 = d.materials?.[1] || {};
      const m3 = d.materials?.[2] || {};

      tr.innerHTML = `
        <td>${d.category || ""}</td>
        <td>${d.rank || ""}</td>
        <td>${d.code || ""}</td>
        <td>${d.name || ""}</td>

        <td>${m1.url ? `<a href="${m1.url}" target="_blank" rel="noopener noreferrer">${m1.title || ""}</a>` : ""}</td>
        <td>${m1.date || ""}</td>

        <td>${m2.url ? `<a href="${m2.url}" target="_blank" rel="noopener noreferrer">${m2.title || ""}</a>` : ""}</td>
        <td>${m2.date || ""}</td>

        <td>${m3.url ? `<a href="${m3.url}" target="_blank" rel="noopener noreferrer">${m3.title || ""}</a>` : ""}</td>
        <td>${m3.date || ""}</td>

        <td>${d.news_list_url ? `<a href="${d.news_list_url}" target="_blank" rel="noopener noreferrer">一覧</a>` : ""}</td>
        <td>${d.time || ""}</td>
      `;

      tbody.appendChild(tr);
    });
  });
