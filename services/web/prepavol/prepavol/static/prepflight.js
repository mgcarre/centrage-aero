let callsign;
let bew = 0;
let frontweight = 0;
let rearweight = 0;
let bagweight = 0;
let bagweight2 = 0;
let mainfuelweight = 0;
let wingfuelweight = 0;
let auxfuelweight = 0;
let auw;
let bemoment = 0;
let frontmoment = 0;
let rearmoment = 0;
let bagmoment = 0;
let bagmoment2 = 0;
let mainfuelmoment = 0;
let wingfuelmoment = 0;
let auxfuelmoment = 0;
let moment;
let cg;
let essence;

function reset_form() {
  const selectfields = [
    "#pax0",
    "#pax1",
    "#pax2",
    "#pax3",
    "#baggage",
    "#baggage2",
    "#mainfuel",
    "#leftwingfuel",
    "#rightwingfuel",
    "#auxfuel",
  ];
  selectfields.forEach(field => {
    const elem = document.querySelector(field)
    elem.selectedIndex = 0
  })
}

function update_totals() {
  auw = [
    bew,
    frontweight,
    rearweight,
    bagweight,
    bagweight2,
    mainfuelweight,
    wingfuelweight,
    auxfuelweight,
  ].reduce((a, b) => a + b);

  moment = [
    bemoment,
    frontmoment,
    rearmoment,
    bagmoment,
    bagmoment2,
    mainfuelmoment,
    wingfuelmoment,
    auxfuelmoment,
  ].reduce((a, b) => a + b);
  cg = moment / auw;

  update_element_HTML("#auw", auw.toFixed(1), "Kg")
  update_element_HTML("#cg", cg.toFixed(2), "m")
  update_element_HTML("#moment", moment.toFixed(0), "Kg.m")
}

function update_element_HTML(elementId, value, unit = "") {
  document.querySelector(elementId).innerHTML = `${value} ${unit}`.trim()
}

async function update_plane() {
  callsign = document.querySelector("#callsign").value;
  plane = planes[callsign];

  req = await fetch(`essence?type=${plane.fuel_name}`)
  essence = await req.json()
  planetype = plane.planetype;
  bew = plane.bew;
  bearm = plane.arms.bew;
  bemoment = bew * bearm;

  update_element_HTML("#planetype", planetype)
  update_element_HTML("#bew", bew.toFixed(0), "Kg")
  update_element_HTML("#bearm", bearm.toFixed(2), "m")
  update_element_HTML("#bemoment", bemoment.toFixed(0), "Kg.m")

  update_front();
  update_rear();
  update_mainfuel();
  update_wingfuel();
  update_auxfuel();
  update_baggage();
  update_baggage2();
  update_totals();
}

function update_front() {
  const w1 = parseInt(document.querySelector("#pax0").value);
  const w2 = parseInt(document.querySelector("#pax1").value);

  if (w1 > 0) {
    document.querySelector(".errors").innerHTML = ""
  }
  frontweight = w1 + w2;
  frontarm = plane.arms.front;
  frontmoment = frontweight * frontarm;

  update_element_HTML("#frontweight", frontweight.toFixed(0), "Kg")
  update_element_HTML("#frontarm", frontarm.toFixed(2), "m");
  update_element_HTML("#frontmoment", frontmoment.toFixed(0), "Kg.m");

  update_totals();
}

function update_rear() {
  const w1 = parseInt(document.querySelector("#pax2").value);
  const w2 = parseInt(document.querySelector("#pax3").value);
  if (plane.arms.rear == 0) {
    document.querySelector("#pax2").selectedIndex = 0
    document.querySelector("#pax3").selectedIndex = 0
  }
  rearweight = w1 + w2;
  reararm = plane.arms.rear;
  rearmoment = rearweight * reararm;

  update_element_HTML("#rearweight", rearweight.toFixed(0), "Kg");
  update_element_HTML("#reararm", reararm.toFixed(2), "m");
  update_element_HTML("#rearmoment", rearmoment.toFixed(0), "Kg.m");

  update_totals();
}

function update_baggage() {
  bagweight = parseInt(document.querySelector("#baggage").value);
  bagarm = plane.arms.baggage;
  bagmoment = bagweight * bagarm;

  update_element_HTML("#bagweight", bagweight.toFixed(0), "Kg");
  update_element_HTML("#bagarm", bagarm.toFixed(2), "m");
  update_element_HTML("#bagmoment", bagmoment.toFixed(0), "Kg.m");

  update_totals();
}

function update_baggage2() {
  bagweight2 = parseInt(document.querySelector("#baggage2").value);
  if (plane.bagmax2 == 0) {
    document.querySelector("#baggage2").selectedIndex = 0
    bagweight2 = 0;
  }
  bagarm2 = plane.arms.baggage2;
  bagmoment2 = bagweight2 * bagarm2;

  update_element_HTML("#bagweight2", bagweight2.toFixed(0), "Kg");
  update_element_HTML("#bagarm2", bagarm2.toFixed(2), "m");
  update_element_HTML("#bagmoment2", bagmoment2.toFixed(0), "Kg.m");

  update_totals();
}

function update_mainfuel() {
  const value = parseFloat(document.querySelector("#mainfuel").value);
  if (plane.maxmainfuel == 0) {
    document.querySelector("#mainfuel").selectedIndex = 0
  }
  mainfuelweight = value * essence?.density;
  mainfuelarm = plane.arms.mainfuel;
  mainfuelmoment = mainfuelweight * mainfuelarm;

  update_element_HTML("#mainfuelmass", mainfuelweight.toFixed(0), "Kg");
  update_element_HTML("#mainfuelarm", mainfuelarm.toFixed(2), "m");
  update_element_HTML("#mainfuelmoment", mainfuelmoment.toFixed(0), "Kg.m");

  update_totals();
}

function update_wingfuel() {
  const w1 = parseInt(document.querySelector("#leftwingfuel").value);
  const w2 = parseInt(document.querySelector("#rightwingfuel").value);
  if (plane.maxwingfuel == 0) {
    document.querySelector("#leftwingfuel").selectedIndex = 0
    document.querySelector("#rightwingfuel").selectedIndex = 0
  }
  wingfuelweight = (w1 + w2) * essence?.density;
  wingfuelarm = plane.arms.wingfuel;
  wingfuelmoment = wingfuelweight * wingfuelarm;

  update_element_HTML("#wingfuelweight", wingfuelweight.toFixed(0), "Kg");
  update_element_HTML("#wingfuelarm", wingfuelarm.toFixed(2), "m");
  update_element_HTML("#wingfuelmoment", wingfuelmoment.toFixed(0), "Kg.m");

  update_totals();
}

function update_auxfuel() {
  const value = parseInt(document.querySelector("#auxfuel").value);

  if (plane.maxauxfuel == 0) {
    document.querySelector("#auxfuel").selectedIndex = 0
  }
  auxfuelweight = value * 0.72;
  auxfuelarm = plane.arms.auxfuel;
  auxfuelmoment = auxfuelweight * auxfuelarm;

  update_element_HTML("#auxfuelmass", auxfuelweight.toFixed(0), "Kg");
  update_element_HTML("#auxfuelarm", auxfuelarm.toFixed(2), "m");
  update_element_HTML("#auxfuelmoment", auxfuelmoment.toFixed(0), "Kg.m");

  update_totals();
}

// Initialization of the form
update_plane();
update_front();
update_rear();
update_baggage();
update_baggage2();
update_mainfuel();
update_wingfuel();
update_auxfuel();

// Event callbacks
const elem = new Map()
elem.set("#callsign", update_plane);
elem.set("#pax0", update_front);
elem.set("#pax1", update_front)
elem.set("#pax2", update_rear);
elem.set("#pax3", update_rear)
elem.set("#baggage", update_baggage);
elem.set("#baggage2", update_baggage2);
elem.set("#mainfuel", update_mainfuel);
elem.set("#leftwingfuel", update_wingfuel);
elem.set("#rightwingfuel", update_wingfuel)
elem.set("#auxfuel", update_auxfuel);
window.addEventListener("DOMContentLoaded", e => {
  elem.forEach((val, key) => {
    document.querySelector(key).addEventListener("change", val)
  })
  document.querySelector("#resetform").addEventListener("click", (e) => {
    e.preventDefault()
    reset_form()
  })
})


