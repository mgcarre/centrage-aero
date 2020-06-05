
$(document).ready(function() {

    var callsign;
    var bew = 0;
    var frontweight = 0;
    var rearweight = 0;
    var bagweight = 0;
    var fuelweight = 0;
    var auxfuelweight = 0;
    var auw;
    var bemoment = 0;
    var frontmoment = 0;
    var rearmoment = 0;
    var bagmoment = 0;
    var fuelmoment = 0;
    var auxfuelmoment = 0;
    var moment;
    var cg;
    
    function reset_form() {
        console.log('IN RESET');
        var selectfields = ['#callsign',
            '#pax0', '#pax1', '#pax2', '#pax3',
            '#baggage',
            '#fuel_gauge', '#auxfuel_gauge'];
        $.each(selectfields, function(index, value) {
            $(value).get(0).selectedIndex = 0;
            $(value).trigger('change');
            console.log($(value).val());
        });
    };

    function update_totals() {
        auw = [bew, frontweight, rearweight, 
                bagweight, fuelweight, auxfuelweight].reduce((a, b)=> a +b);
        console.log('TOTALS', fuelweight, auw)
        moment = [bemoment, frontmoment, rearmoment,
                bagmoment, fuelmoment, auxfuelmoment].reduce((a, b)=> a + b);
        cg = moment / auw;

        $('#auw').html(auw.toFixed(1) + 'kg');
        $('#cg').html(cg.toFixed(2) + 'm');
        $('#moment').html(moment.toFixed(0) + 'kg.m');
    };

    function update_plane(){
        callsign = $('#callsign').val();
        plane = planes[callsign];
        console.log("IN UPDATE PLANE", plane)
        
        planetype = plane.planetype;
        bew = plane.bew;
        bearm = plane.arms.bew;
        bemoment = (bew * bearm);

        $('#planetype').html(planetype);
        $('#bew').html(bew.toFixed(0) + 'kg');
        $('#bearm').html(bearm.toFixed(2) + 'm');
        $('#bemoment').html(bemoment.toFixed(0) + 'kg.m');

        update_front();
        update_rear();
        update_fuel();
        update_auxfuel();
        update_totals();
    }

    function update_front() {
        console.log("PAX", plane);//.arms.front);
        var w1 = parseInt($('#pax0').val());
        var w2 = parseInt($('#pax1').val());

        if (w1 > 0) {
            $('.errors').empty();
        }
        frontweight = w1 + w2;
        frontarm = plane.arms.front;
        frontmoment = frontweight * frontarm;

        $("#frontweight").html(frontweight.toFixed(0) + 'kg');
        $('#frontarm').html(frontarm.toFixed(2) + 'm');
        $('#frontmoment').html(frontmoment.toFixed(0) + 'kg.m');

        update_totals();
    }

    function update_rear() {
        console.log(plane.arms.rear);
        var w1 = parseInt($('#pax2').val());
        var w2 = parseInt($('#pax3').val());
        rearweight = w1 + w2;
        reararm = plane.arms.rear;
        rearmoment = rearweight * reararm;

        $("#rearweight").html(rearweight.toFixed(0) + 'kg');
        $('#reararm').html(reararm.toFixed(2) + 'm');
        $('#rearmoment').html(rearmoment.toFixed(0) + 'kg.m');

        update_totals();
    }

    function update_baggage() {
        console.log(plane.arms.baggage);
        bagweight = parseInt($('#baggage').val());
        bagarm = plane.arms.baggage;
        bagmoment = bagweight * bagarm;

        $("#bagweight").html(bagweight.toFixed(0) + 'kg');
        $('#bagarm').html(bagarm.toFixed(2) + 'm');
        $('#bagmoment').html(bagmoment.toFixed(0) + 'kg.m');

        update_totals();
    }

    function update_fuel() {
        console.log("IN UPDATE FUEL", plane.arms.fuel);
        var gauge = parseFloat($('#fuel_gauge').val());
        console.log(gauge, plane.maxfuel)
        fuelweight = gauge * plane.maxfuel / 4 * .72;
        fuelarm = plane.arms.fuel;
        fuelmoment = fuelweight * fuelarm;

        $("#fuelmass").html(fuelweight.toFixed(0) + 'kg');
        $('#fuelarm').html(fuelarm.toFixed(2) + 'm');
        $('#fuelmoment').html(fuelmoment.toFixed(0) + 'kg.m');

        update_totals();
    }

    function update_auxfuel() {
        var value = parseInt($('#auxfuel_gauge').val());
        console.log("IN UPDATE_AUXFUEL", value, plane.maxauxfuel, value > plane.maxauxfuel)
        if (plane.maxauxfuel == 0) {
            $('#auxfuel_gauge').val(0);
        }
        auxfuelweight = value * plane.maxauxfuel / 4 * .72;
        auxfuelarm = plane.arms.auxfuel;
        auxfuelmoment = auxfuelweight * auxfuelarm;

        $("#auxfuelmass").html(auxfuelweight.toFixed(0) + 'kg');
        $('#auxfuelarm').html(auxfuelarm.toFixed(2) + 'm');
        $('#auxfuelmoment').html(auxfuelmoment.toFixed(0) + 'kg.m');

        update_totals();
    }

    // Initialization of the form
    update_plane();
    update_front();
    update_rear();
    update_baggage();
    update_fuel();
    update_auxfuel();

    // Event callbacks
    $('#callsign').on('change', update_plane);
    $('#pax0, #pax1').on('change', update_front);
    $('#pax2, #pax3').on('change', update_rear);
    $('#baggage').on('change', update_baggage);
    $('#fuel_gauge').on('change', update_fuel);
    $('#auxfuel_gauge').on('change', update_auxfuel);
    $('#resetform').on('click', reset_form);
    
});