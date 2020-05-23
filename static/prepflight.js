$(document).ready(function() {
    var name;
    var plane;

    //alert(planes)
    $('#plane').on('change', function(){
        var name = $('#plane').val();
        var plane = planes[name];
        var planetype = plane.planetype;
        var bew = plane.bew.toFixed(3);
        var bearm = plane.arms.bew;
        var bemoment = (bew * bearm).toFixed(3);

        $('#planetype').html(planetype);
        $('#bew').html(bew);
        $('#bearm').html(bearm);
        $('#bemoment').html(bemoment);
    });

    $('#pax0, #pax1').on('change', function(){
        var name = $('#plane').val();
        var plane = planes[name];
        console.log(plane.arms.front);
        var w1 = parseInt($('#pax0').val());
        var w2 = parseInt($('#pax1').val());
        var frontweight = w1 + w2;
        var frontarm = plane.arms.front;
        var frontmoment = frontweight * frontarm;

        $("#frontweight").html(frontweight.toFixed(3));
        $('#frontarm').html(frontarm);
        $('#frontmoment').html(frontmoment.toFixed(3));
    });

    $('#pax2, #pax3').on('change', function(){
        var name = $('#plane').val();
        var plane = planes[name];
        console.log(plane.arms.rear);
        var w1 = parseInt($('#pax2').val());
        var w2 = parseInt($('#pax3').val());
        var rearweight = w1 + w2;
        var reararm = plane.arms.rear;
        var rearmoment = rearweight * reararm;

        $("#rearweight").html(rearweight.toFixed(3));
        $('#reararm').html(reararm);
        $('#rearmoment').html(rearmoment.toFixed(3));
    });

    $('#baggage').on('change', function(){
        var name = $('#plane').val();
        var plane = planes[name];
        console.log(plane.arms.baggage);
        var weight = parseInt($(this).val());
        var arm = plane.arms.baggage;
        var moment = weight * arm;

        $("#bagweight").html(weight.toFixed(3));
        $('#bagarm').html(arm);
        $('#bagmoment').html(moment.toFixed(3));
    });
});