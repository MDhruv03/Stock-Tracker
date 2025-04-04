function sortTable(colIndex, header) {
  const table = document.getElementById("stocksTable");
  const headers = table.querySelectorAll("th");
  const tbody = table.querySelector("tbody");
  const rows = Array.from(tbody.rows);
  const isAscending = !header.classList.contains("sort-asc");
  
  // Reset all headers
  headers.forEach(h => {
      h.classList.remove("sort-asc", "sort-desc");
      const indicator = h.querySelector(".sort-indicator");
      if (indicator) {
          indicator.textContent = "▼";
      }
  });
  
  // Set current header state
  header.classList.add(isAscending ? "sort-asc" : "sort-desc");
  const currentIndicator = header.querySelector(".sort-indicator");
  if (currentIndicator) {
      currentIndicator.textContent = isAscending ? "▲" : "▼";
  }
  
  // Sort rows
  rows.sort((a, b) => {
      const cellA = a.cells[colIndex];
      const cellB = b.cells[colIndex];
      
      if (!cellA || !cellB) return 0;
      
      let valA = cellA.textContent.trim();
      let valB = cellB.textContent.trim();
      
      // Remove currency symbols if present
      valA = valA.replace(/[^\d.-]/g, '');
      valB = valB.replace(/[^\d.-]/g, '');
      
      // Check if values are numeric
      const numA = parseFloat(valA);
      const numB = parseFloat(valB);
      
      if (!isNaN(numA)) {
          return (numA - (isNaN(numB) ? 0 : numB)) * (isAscending ? 1 : -1);
      } else {
          return valA.localeCompare(valB) * (isAscending ? 1 : -1);
      }
  });
  
  // Reattach sorted rows
  rows.forEach(row => tbody.appendChild(row));
}
  
  // Filter stocks with loading state
  function filterStocks() {
    const minEps = document.getElementById("min_eps").value;
    const maxPe = document.getElementById("max_pe").value;
    const resultsDiv = document.getElementById("stock-results");
    
    resultsDiv.innerHTML = "<div class='loading' style='height: 100px;'></div>";
    
    fetch("/buy-stocks/filter-stocks", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ min_eps: minEps, max_pe: maxPe })
    })
    .then(response => response.json())
    .then(data => {
      if (data.length === 0) {
        resultsDiv.innerHTML = "<div class='empty-state'>No stocks match your filters</div>";
        return;
      }
      
      let html = `
        <table class="analytics-table">
          <thead>
            <tr>
              <th>Ticker</th>
              <th>Name</th>
              <th>EPS Growth</th>
              <th>P/E Ratio</th>
            </tr>
          </thead>
          <tbody>
      `;
      
      data.forEach(stock => {
        html += `
          <tr>
            <td>
              <a href="{{ url_for('stock_details.stock_page', ticker='') }}${stock.ticker}" class="stock-link">
                ${stock.ticker}
              </a>
            </td>
            <td>${stock.name}</td>
            <td>${stock.eps}%</td>
            <td>${stock.pe}</td>
          </tr>
        `;
      });
      
      html += `</tbody></table>`;
      resultsDiv.innerHTML = html;
    })
    .catch(error => {
      console.error("Error filtering stocks:", error);
      resultsDiv.innerHTML = `<div class='empty-state'>Error loading filtered stocks</div>`;
    });
  }
  
  // Fetch top movers with separate gainers/losers display
  function fetchTopMovers() {
    const gainersDiv = document.getElementById("top-gainers");
    const losersDiv = document.getElementById("top-losers");
    
    gainersDiv.innerHTML = "<div class='loading' style='height: 100px;'></div>";
    losersDiv.innerHTML = "<div class='loading' style='height: 100px;'></div>";
    
    fetch("/buy-stocks/top-movers")
      .then(response => response.json())
      .then(data => {
        // Render gainers
        if (data.gainers.length === 0) {
          gainersDiv.innerHTML = "<div class='empty-state'>No gainers data available</div>";
        } else {
          let gainersHtml = `
            <table class="analytics-table">
              <thead>
                <tr>
                  <th>Stock</th>
                  <th>Change %</th>
                </tr>
              </thead>
              <tbody>
          `;
          
          data.gainers.slice(0, 5).forEach(item => {
            gainersHtml += `
              <tr>
                <td>${item.name}</td>
                <td class="gain">+${item.percentage_change}%</td>
              </tr>
            `;
          });
          
          gainersHtml += `</tbody></table>`;
          gainersDiv.innerHTML = gainersHtml;
        }
        
        // Render losers
        if (data.losers.length === 0) {
          losersDiv.innerHTML = "<div class='empty-state'>No losers data available</div>";
        } else {
          let losersHtml = `
            <table class="analytics-table">
              <thead>
                <tr>
                  <th>Stock</th>
                  <th>Change %</th>
                </tr>
              </thead>
              <tbody>
          `;
          
          data.losers.slice(0, 5).forEach(item => {
            losersHtml += `
              <tr>
                <td>${item.name}</td>
                <td class="loss">${item.percentage_change}%</td>
              </tr>
            `;
          });
          
          losersHtml += `</tbody></table>`;
          losersDiv.innerHTML = losersHtml;
        }
      })
      .catch(error => {
        console.error("Error fetching top movers:", error);
        gainersDiv.innerHTML = "<div class='empty-state'>Error loading gainers</div>";
        losersDiv.innerHTML = "<div class='empty-state'>Error loading losers</div>";
      });
  }
  
  // Fetch highest EPS growth
  function fetchHighestEPSGrowth() {
    const epsDiv = document.getElementById("eps-results");
    epsDiv.innerHTML = "<div class='loading' style='height: 100px;'></div>";
    
    fetch("/buy-stocks/highest-eps-growth")
      .then(response => response.json())
      .then(data => {
        if (data.length === 0) {
          epsDiv.innerHTML = "<div class='empty-state'>No EPS growth data available</div>";
          return;
        }
        
        let html = `
          <table class="analytics-table">
            <thead>
              <tr>
                <th>Ticker</th>
                <th>Name</th>
                <th>EPS Growth</th>
              </tr>
            </thead>
            <tbody>
        `;
        
        data.forEach(item => {
          html += `
            <tr>
              <td>
                <a href="{{ url_for('stock_details.stock_page', ticker='') }}${item.ticker}" class="stock-link">
                  ${item.ticker}
                </a>
              </td>
              <td>${item.name}</td>
              <td class="gain">${item.eps_growth}%</td>
            </tr>
          `;
        });
        
        html += `</tbody></table>`;
        epsDiv.innerHTML = html;
      })
      .catch(error => {
        console.error("Error fetching EPS growth:", error);
        epsDiv.innerHTML = "<div class='empty-state'>Error loading EPS data</div>";
      });
  }
  
  // Fetch undervalued stocks
  function fetchUndervaluedStocks() {
    const undervaluedDiv = document.getElementById("undervalued-results");
    undervaluedDiv.innerHTML = "<div class='loading' style='height: 100px;'></div>";
    
    fetch("/buy-stocks/undervalued-stocks")
      .then(response => response.json())
      .then(data => {
        if (data.length === 0) {
          undervaluedDiv.innerHTML = "<div class='empty-state'>No undervalued stocks found</div>";
          return;
        }
        
        let html = `
          <table class="analytics-table">
            <thead>
              <tr>
                <th>Ticker</th>
                <th>Name</th>
                <th>P/E</th>
                <th>EPS Growth</th>
              </tr>
            </thead>
            <tbody>
        `;
        
        data.forEach(item => {
          html += `
            <tr>
              <td>
                <a href="{{ url_for('stock_details.stock_page', ticker='') }}${item.ticker}" class="stock-link">
                  ${item.ticker}
                </a>
              </td>
              <td>${item.name}</td>
              <td>${item.pe_ratio}</td>
              <td>${item.eps_growth}%</td>
            </tr>
          `;
        });
        
        html += `</tbody></table>`;
        undervaluedDiv.innerHTML = html;
      })
      .catch(error => {
        console.error("Error fetching undervalued stocks:", error);
        undervaluedDiv.innerHTML = "<div class='empty-state'>Error loading data</div>";
      });
  }
  
  // Fetch most traded stocks
  function fetchMostTraded() {
    const tradedDiv = document.getElementById("traded-results");
    tradedDiv.innerHTML = "<div class='loading' style='height: 100px;'></div>";
    
    fetch("/buy-stocks/most-traded-stocks")
      .then(response => response.json())
      .then(data => {
        if (data.length === 0) {
          tradedDiv.innerHTML = "<div class='empty-state'>No trading data available</div>";
          return;
        }
        
        let html = `
          <table class="analytics-table">
            <thead>
              <tr>
                <th>Ticker</th>
                <th>Name</th>
                <th>Volume</th>
              </tr>
            </thead>
            <tbody>
        `;
        
        data.forEach(item => {
          html += `
            <tr>
              <td>
                <a href="{{ url_for('stock_details.stock_page', ticker='') }}${item.ticker}" class="stock-link">
                  ${item.ticker}
                </a>
              </td>
              <td>${item.name}</td>
              <td>${item.total_volume.toLocaleString()}</td>
            </tr>
          `;
        });
        
        html += `</tbody></table>`;
        tradedDiv.innerHTML = html;
      })
      .catch(error => {
        console.error("Error fetching most traded:", error);
        tradedDiv.innerHTML = "<div class='empty-state'>Error loading data</div>";
      });
  }
  
  // Initialize data on load
  document.addEventListener('DOMContentLoaded', function() {
    fetchTopMovers();
    fetchHighestEPSGrowth();
    fetchUndervaluedStocks();
    fetchMostTraded();
    
    // Add animation to buttons on click
    document.querySelectorAll('.btn').forEach(btn => {
      btn.addEventListener('click', function() {
        this.classList.add('animate__animated', 'animate__pulse');
        setTimeout(() => {
          this.classList.remove('animate__animated', 'animate__pulse');
        }, 500);
      });
    });
  });