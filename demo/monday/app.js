"use strict";
(() => {
  const data = window.DEMO_DATA;
  const seeds = document.querySelector("#actual-seeds");
  data.v2.seed_decisions.forEach(seed => {
    const row = document.createElement("tr");
    const ore = seed.ore_objectives;
    [seed.training_seed, `${ore["0"].positive_episode_count}/160`, `${ore["1"].positive_episode_count}/160`,
      `${ore["0"].distinct_positive_values}/${ore["1"].distinct_positive_values}`, "FAIL"].forEach((value, index) => {
      const cell = document.createElement("td"); cell.textContent = value;
      if (index === 4) cell.className = "fail";
      row.appendChild(cell);
    });
    seeds.appendChild(row);
  });
  const vectors = [{name:"A", r:[10,1]}, {name:"B", r:[6,6]}, {name:"C", r:[1,10]}];
  const slider = document.querySelector("#weight");
  function utility() {
    const w = Number(slider.value) / 100;
    document.querySelector("#weight-label").textContent = w.toFixed(2);
    document.querySelector("#formula").textContent = `u = ${w.toFixed(2)} × r₀ + ${(1-w).toFixed(2)} × r₁`;
    const values = vectors.map(v => w*v.r[0] + (1-w)*v.r[1]);
    const best = Math.max(...values); const rows = document.querySelector("#utility-rows"); rows.replaceChildren();
    vectors.forEach((v,i) => {
      const row = document.createElement("tr"); if (Math.abs(values[i]-best)<1e-9) row.className="winner";
      [v.name, `(${v.r.join(", ")})`, values[i].toFixed(2)].forEach(value => {
        const td=document.createElement("td");td.textContent=value;row.appendChild(td);
      }); rows.appendChild(row);
    });
    document.querySelector("#choice").textContent = `Lựa chọn trong ví dụ giả định: ${vectors.filter((v,i)=>Math.abs(values[i]-best)<1e-9).map(v=>v.name).join(", ")}.`;
  }
  slider.addEventListener("input",utility); utility();
  const scenario = document.querySelector("#scenario");
  function qualify() {
    const cases = {zero:[[0,0],[0,0],[0,0]], "one-fails":[[8,2],[0,0],[8,2]], "all-pass":[[8,2],[8,2],[8,2]]};
    const selected = cases[scenario.value]; const passed=selected.every(([count,distinct])=>count>=8&&distinct>=2);
    const result=document.querySelector("#scenario-result"); result.textContent=passed?"PASS trong tình huống giả":"FAIL trong tình huống giả";
    result.classList.toggle("pass",passed);
    document.querySelector("#scenario-details").textContent=passed?"Cả 3 seed đều thỏa hai điều kiện cho mỗi ore objective.":"Chỉ cần một seed không thỏa là cả qualification không đạt.";
    const panel=document.querySelector("#scenario-seeds"); panel.replaceChildren();
    selected.forEach(([count,distinct],i)=>{const p=document.createElement("p");p.className="scenario-line";p.textContent=`Seed giả ${i+1}: ${count}/160 dương, ${distinct} giá trị dương phân biệt cho mỗi ore objective.`;panel.appendChild(p);});
  }
  scenario.addEventListener("change",qualify);qualify();
})();
