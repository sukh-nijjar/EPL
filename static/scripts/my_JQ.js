$(document).ready(function() {

    $('#submitSaveTeam').on('click', function(e) {
        e.preventDefault();
        if ( $('.error').length ){
          $('.error').remove();
        }
        var teamName = $('#teamName').val();
        if (teamName.trim().length > 0){
          $('#create_team').submit();
        }
        else {
          $('section').prepend('<h3 id="UI_Msg" class="error">Team name is mandatory</h3>');
          toggle_UI_Msg();
        }
     });

    $('#submitDeleteAllTeams').on('click', function(e) {
           e.preventDefault();
           $("#dialog-confirm").dialog({
             title: "Delete all teams?",
             resizable: false,
             //autoOpen: false,
             height: "auto",
             width: 400,
             modal: true,
             buttons: {
               "No, do not delete all teams": function() {
                 $( this ).dialog( "close" );
               },
               "Yes, delete all teams": function() {
                 $("#deleteAllTeams").submit();
               }
             } //end buttons
           });
    });

    $('tr').delegate('td.action_link', 'click', function(e) {
      $this = $(this);
      var action_type = $this.find('a').text();
      if (action_type === 'Edit'){
          if ($(this).closest('tr').hasClass('fixture')){
            // alert("Fixture class row");
            $(this).closest('tr').css('background-color','#44c154').find('input').prop('disabled', false);
            $(this).after('<td class="action_link"><a class="AL_cancel" href="#">Cancel</a></td>');
            $(this).after('<td class="action_link"><a class="AL_save" href="#">Save</a></td>');
            $(this).remove();
          } else /*result*/ {
            var hftg = $(this).closest('tr').find('[name=hftg]').text();
            var hhtg = $(this).closest('tr').find('[name=hhtg]').text();
            var ahtg = $(this).closest('tr').find('[name=ahtg]').text();
            var aftg = $(this).closest('tr').find('[name=aftg]').text();
            // alert("It's a result class row");
            $(this).closest('tr').css('background-color','#44c154');
            $(this).closest('tr').each(function(){
              $(this).find('td').not('.action_link, .team').remove();
            });
            $(this).after('<td class="action_link"><a class="AL_cancel" href="#">Cancel</a></td>');
            $(this).after('<td class="action_link"><a class="AL_delete" href="#">Delete</a></td>');
            $(this).after('<td class="action_link"><a class="AL_save" href="#">Save</a></td>');
            $(this).closest('tr').find('td:nth-child(1)').after('<td name="hftg"><input min="0" name="hftg" type="number" value="' + hftg + '"/></td>');
            $(this).closest('tr').find('td:nth-child(2)').after('<td name="hhtg"><input min="0" name="hhtg" type="number" value="' + hhtg + '"/></td>');
            $(this).closest('tr').find('td:nth-child(3)').after('<td name="ahtg"><input min="0" name="ahtg" type="number" value="' + ahtg + '"/></td>');
            $(this).closest('tr').find('td:nth-child(4)').after('<td name="aftg"><input min="0" name="aftg" type="number" value="' + aftg + '"/></td>');
            $(this).remove();
          }
        } //end if action type is *EDIT*
        if (action_type === 'Cancel'){
          location.reload(true);
        } //end if action type is *CANCEL*
        if (action_type === 'Save'){
          $.ajax({
            data :  {
              home_team : $(this).closest('tr').find('[name=home_team]').text(),
              hftg : $(this).closest('tr').find('td input[name=hftg]').val(),
              hhtg : $(this).closest('tr').find('td input[name=hhtg]').val(),
              ahtg : $(this).closest('tr').find('td input[name=ahtg]').val(),
              aftg : $(this).closest('tr').find('td input[name=aftg]').val(),
              away_team : $(this).closest('tr').find('[name=away_team]').text()
            },
            type : 'PUT',
            url : '/update_score/'
          })
          .done(function(data) {
            if (data.done) {
              $('section').prepend('<h3 id="UI_Msg" class="success_msg">' + data.done +'</h3>');
              toggle_UI_Msg();
            }
            else {
              // alert(data.error);
              $('section').prepend('<h3 id="UI_Msg" class="error">' + data.error + '</h3>');
              toggle_UI_Msg();
            }
          })
        } //end if action type is *SAVE*
        if (action_type === 'Delete'){
          alert("DELETE CALLED")
          $.ajax({
            data : {
              home_team : $(this).closest('tr').find('[name=home_team]').text(),
              away_team : $(this).closest('tr').find('[name=away_team]').text()
            },
            type : 'DELETE',
            url : '/delete_result/'
          })
          .done(function(data) {
            if (data.done) {
              $('section').prepend('<h3 id="UI_Msg" class="success_msg">' + data.done +'</h3>');
              toggle_UI_Msg();
            }
          })
        } //end if action type is *DELETE*
    }); //function end

    var team = $('#team_details_name').text();
    $("tr.result_row").each(function() {
      $this = $(this);
      var row_team = $this.find("td.home_team").text();
      var home = $this.find("td.home").text();
      var away = $this.find("td.away").text();
      if (row_team === team){
        if (home > away) {
          $(this).find('td.result_type').append('<img src="/static/images/win.png"/>');
        } else if (away > home) {
          $(this).find('td.result_type').append('<img src="/static/images/loss.png"/>');
        } else {
          $(this).find('td.result_type').append('<img src="/static/images/draw.png"/>');
        }
      }
      if (row_team != team) {
        if (home > away) {
          $(this).find('td.result_type').append('<img src="/static/images/loss.png"/>');
        } else if (away > home) {
          $(this).find('td.result_type').append('<img src="/static/images/win.png"/>');
        } else {
          $(this).find('td.result_type').append('<img src="/static/images/draw.png"/>');
        }
      }
    });

       $( ".selectmenu" ).selectmenu();
       $(".spinner").spinner({
          min: 0
       });

       $( "#menu" ).menu();
       $(" #GDToolTip ").tooltip();


      $('.error').fadeIn("slow");
      $('.feedback').fadeIn("slow");
      $('.success_msg').fadeIn("slow");
      $('.warning').fadeIn("slow");

});//end top document.ready function

function toggle_UI_Msg(){
  // $('section').prepend('<h3 id="UI_Msg" class="success_msg">' + data.done +'</h3>');
  $('#UI_Msg').slideDown();
  window.setTimeout(function(){
       $('#UI_Msg').slideUp(400,function(){
         location.reload(true);
       })},3000);
}

//set focus on team name input on create team form
// document.getElementById("teamName").focus();
