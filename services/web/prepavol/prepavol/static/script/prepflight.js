class ACFT {
  constructor () {
    this.callsign = ""
    this.bew = 0
    this.frontweight = 0
    this.rearweight = 0
    this.bagweight = 0
    this.bagarm = 0
    this.bagweight2 = 0
    this.bagarm2 = 0
    this.mainfuelweight = 0
    this.wingfuelweight = 0
    this.auxfuelweight = 0
    this.bearm = 0
    this.mainfuelarm = 0
    this.wingfuelarm = 0
    this.auxfuelarm = 0
  }
  get auw() {
    return [
      this.bew,
      this.frontweight,
      this.rearweight,
      this.bagweight,
      this.bagweight2,
      this.mainfuelweight,
      this.wingfuelweight,
      this.auxfuelweight,
    ].reduce((a, b) => a + b)
  }
  get moment() {
    return [
      this.bemoment,
      this.frontmoment,
      this.rearmoment,
      this.bagmoment,
      this.bagmoment2,
      this.mainfuelmoment,
      this.wingfuelmoment,
      this.auxfuelmoment,
    ].reduce((a, b) => a + b)
  }
  get cg() {
    return this.moment / this.auw
  }
  get bemoment() {
    return this.bew * this.bearm
  }
  get frontmoment() {
    return this.frontweight * this.frontarm
  }
  get rearmoment() {
    return this.rearweight * this.reararm
  }
  get bagmoment() {
    return this.bagweight * this.bagarm
  }
  get bagmoment2() {
    return this.bagweight2 * this.bagarm2
  }
  get mainfuelmoment() {
    return this.mainfuelweight * this.mainfuelarm
  }
  get wingfuelmoment() {
    return this.wingfuelweight * this.wingfuelarm
  }
  get auxfuelmoment() {
    return this.auxfuelweight * this.auxfuelarm
  }
}
class ACFTParams {
  constructor () {
    this.arms = null
    this.bagmax = 0
    this.bagmax2 = 0
    this.bew = 0
    this.envelope = []
    this.fuel_name = ""
    this.fuelrate = 0
    this.maxauxfuel = 0
    this.maxmainfuel = 0
    this.maxwingfuel = 0
    this.mtow = 0
    this.planetype = ""
    this.sumbagmax = 0
    this.unusable_mainfuel = 0
    this.unusable_wingfuel = 0
  }
  populate(elem) {
    Object.assign(this, elem)
  }
}
let avion = new ACFT()
let params = new ACFTParams()
let essence

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
    "#tkalt",
    "#ldalt",
    "#tktemp",
    "#ldtemp",
    "#tkqnh",
    "#ldqnh"
  ];
  selectfields.forEach(field => {
    const elem = document.querySelector(field)
    elem.selectedIndex = 0
  })
  document.getElementById('tkaltinput').value = ''
  document.getElementById('ldaltinput').value = ''
}

function update_totals() {
  update_element_HTML("#auw", avion.auw.toFixed(1), "Kg")
  update_element_HTML("#cg", avion.cg.toFixed(2), "m")
  update_element_HTML("#moment", avion.moment.toFixed(0), "Kg.m")
}

function update_element_HTML(elementId, value, unit = "") {
  document.querySelector(elementId).innerHTML = `${value} ${unit}`.trim()
}

async function update_plane() {
  avion = new ACFT()
  params = new ACFTParams()
  avion.callsign = document.querySelector("#callsign").value;
  params.populate(planes[avion.callsign])

  const req = await fetch(`essence?type=${params.fuel_name}`)
  essence = await req.json()
  avion.bew = params.bew;
  avion.bearm = params.arms.bew;

  update_element_HTML("#planetype", params.planetype)
  update_element_HTML("#bew", avion.bew.toFixed(0), "Kg")
  update_element_HTML("#bearm", avion.bearm.toFixed(2), "m")
  update_element_HTML("#bemoment", avion.bemoment.toFixed(0), "Kg.m")

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

  avion.frontweight = w1 + w2;
  avion.frontarm = params.arms.front;

  update_element_HTML("#frontweight", avion.frontweight.toFixed(0), "Kg")
  update_element_HTML("#frontarm", avion.frontarm.toFixed(2), "m");
  update_element_HTML("#frontmoment", avion.frontmoment.toFixed(0), "Kg.m");

  update_totals();
}

function update_rear() {
  const w1 = parseInt(document.querySelector("#pax2").value);
  const w2 = parseInt(document.querySelector("#pax3").value);
  if (params.arms.rear == 0) {
    document.querySelector("#pax2").selectedIndex = 0
    document.querySelector("#pax3").selectedIndex = 0
  }
  avion.rearweight = w1 + w2;
  avion.reararm = params.arms.rear;

  update_element_HTML("#rearweight", avion.rearweight.toFixed(0), "Kg");
  update_element_HTML("#reararm", avion.reararm.toFixed(2), "m");
  update_element_HTML("#rearmoment", avion.rearmoment.toFixed(0), "Kg.m");

  update_totals();
}

function update_baggage() {
  avion.bagweight = parseInt(document.querySelector("#baggage").value);
  avion.bagarm = params.arms.baggage;

  update_element_HTML("#bagweight", avion.bagweight.toFixed(0), "Kg");
  update_element_HTML("#bagarm", avion.bagarm.toFixed(2), "m");
  update_element_HTML("#bagmoment", avion.bagmoment.toFixed(0), "Kg.m");

  update_totals();
}

function update_baggage2() {
  avion.bagweight2 = parseInt(document.querySelector("#baggage2").value);
  if (params.bagmax2 == 0) {
    document.querySelector("#baggage2").selectedIndex = 0
    avion.bagweight2 = 0;
  }
  avion.bagarm2 = params.arms.baggage2;

  update_element_HTML("#bagweight2", avion.bagweight2.toFixed(0), "Kg");
  update_element_HTML("#bagarm2", avion.bagarm2.toFixed(2), "m");
  update_element_HTML("#bagmoment2", avion.bagmoment2.toFixed(0), "Kg.m");

  update_totals();
}

function update_mainfuel() {
  const value = parseFloat(document.querySelector("#mainfuel").value);
  if (params.maxmainfuel == 0) {
    document.querySelector("#mainfuel").selectedIndex = 0
  }
  avion.mainfuelweight = value * essence?.density;
  avion.mainfuelarm = params.arms.mainfuel;

  update_element_HTML("#mainfuelmass", avion.mainfuelweight.toFixed(0), "Kg");
  update_element_HTML("#mainfuelarm", avion.mainfuelarm.toFixed(2), "m");
  update_element_HTML("#mainfuelmoment", avion.mainfuelmoment.toFixed(0), "Kg.m");

  update_totals();
}

function update_wingfuel() {
  const w1 = parseInt(document.querySelector("#leftwingfuel").value);
  const w2 = parseInt(document.querySelector("#rightwingfuel").value);
  if (params.maxwingfuel == 0) {
    document.querySelector("#leftwingfuel").selectedIndex = 0
    document.querySelector("#rightwingfuel").selectedIndex = 0
  }
  avion.wingfuelweight = (w1 + w2) * essence?.density;
  avion.wingfuelarm = params.arms.wingfuel;

  update_element_HTML("#wingfuelweight", avion.wingfuelweight.toFixed(0), "Kg");
  update_element_HTML("#wingfuelarm", avion.wingfuelarm.toFixed(2), "m");
  update_element_HTML("#wingfuelmoment", avion.wingfuelmoment.toFixed(0), "Kg.m");

  update_totals();
}

function update_auxfuel() {
  const value = parseInt(document.querySelector("#auxfuel").value);

  if (params.maxauxfuel == 0) {
    document.querySelector("#auxfuel").selectedIndex = 0
  }
  avion.auxfuelweight = value * essence?.density;
  avion.auxfuelarm = params.arms.auxfuel;

  update_element_HTML("#auxfuelmass", avion.auxfuelweight.toFixed(0), "Kg");
  update_element_HTML("#auxfuelarm", avion.auxfuelarm.toFixed(2), "m");
  update_element_HTML("#auxfuelmoment", avion.auxfuelmoment.toFixed(0), "Kg.m");

  update_totals();
}

async function update_ad_alt(event) {
  event.preventDefault()
  event.stopPropagation()
  const elem = event.target
  const title = document.getElementById(`${elem.id.slice(0, 2)}title`)
  if (elem.value.length === 4) {
    const req = await fetch(`/ad?code=${elem.value.toUpperCase()}`)
    const res = await req.json()
    const l = res.alt.toString().length
    const alt = Math.pow(10, l - 1) * Math.round((res.alt * Math.pow(10, -(l))) * 10)
    document.getElementById(elem.id.replace('input', '')).value = alt
    title.innerHTML = res.nom
    res.statut.toLowerCase().indexOf('milit') > -1 ? title.classList.add('is-danger') : false
  } else {
    document.getElementById(`${elem.id.slice(0, 2)}title`).innerHTML = "?"
    title.classList.remove('is-danger')
  }
}

async function validate_fields(event) {
  event.preventDefault()
  const form = new FormData(document.getElementById('balance'))
  const validate = await fetch("/validate", {
    method: "POST",
    body: form
  })
  document.querySelectorAll(".input.is-danger").forEach(elem => elem.classList.remove("is-danger"))
  if (validate.status == 200) {
    const data = await validate.json()
    const fields = Object.keys(data)
    fields.forEach(field => {
      document.getElementById(field).classList.add("is-danger")
    })
  }
  if (validate.status == 204) {
    console.info("No errors")
    document.forms[0].submit.disabled = false
  }
}

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
  document.querySelectorAll("#perf input").forEach(elem => elem.addEventListener("input", e => update_ad_alt(e)))
  update_plane();
  update_front();
  update_rear();
  update_baggage();
  update_baggage2();
  update_mainfuel();
  update_wingfuel();
  update_auxfuel();
  document.forms[0].addEventListener("change", (e) => validate_fields(e))
})