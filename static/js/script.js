// Function to handle opening the navigation sidebar
function openNav() {
    document.getElementById("navbar").style.width = "250px";
}

// Function to handle closing the navigation sidebar
function closeNav() {
    document.getElementById("navbar").style.width = "0";
}

// Calendar JS logic below

//debugging check to see if calendar loads properly
console.log('FullCalendar is:', typeof FullCalendar !== 'undefined' ? 'Loaded' : 'Not loaded');

document.addEventListener('DOMContentLoaded', function () {
    var calendarEl = document.getElementById('calendar');
    var calendar = new FullCalendar.Calendar(calendarEl, {
        schedulerLicenseKey: 'CC-Attribution-NonCommercial-NoDerivatives',
        initialView: 'dayGridMonth',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        events: calendarEvents.map(event => ({
            title: event.title,
            start: event.start_at,
        })),
        dateClick: function(info) {
            // Populate the modal for new event
            $('#dueDate').val(info.dateStr);
            $('#eventModal').modal('show');
        },
        eventClick: function(info) {
            var eventObj = info.event;
            $('#editAssignmentName').val(eventObj.title);
            $('#editDueDate').val(eventObj.start.toISOString().substring(0, 10));
            // Populate other fields if necessary
            $('#editEventModal').modal('show');
        }
    });

    calendar.render();

    // Separate click handler for updating the event
    $('#updateEvent').on('click', function() {
        // Ensure eventObj is available here
        var eventObj = calendar.getEventById($('#eventId').val()); 
        if (!eventObj) {
            console.error('Event not found');
            return;
        }

        var updatedEventData = {
            event_id: eventObj.id,
            title: $('#editAssignmentName').val(),
            start_date: $('#editDueDate').val() + 'T' + ($('#editEventTime').val() || '00:00'), // Adjust as necessary
            
        };

        
        

        $('#editEventModal').modal('hide');
    });



    calendar.render();

    // Handle saving new event from the modal
    $('#saveEvent').on('click', function() {
        var eventType = $('#eventType').val();
        var assignmentName = $('#assignmentName').val();
        var dueDate = $('#dueDate').val();
        var eventTime = $('#eventTime').val();
        var eventLocation = $('#eventLocation').val();
        var eventClass = $('#eventClass').val();
    
        var eventData = {
            title: assignmentName + ' - ' + eventType,
            start: dueDate + 'T' + (eventTime || '00:00'), // If time is not provided, default to '00:00'
            location: eventLocation,
            className: eventClass
            
        };
    
        // Ensure all necessary fields are filled
        if (eventData.title && eventData.start) {
            calendar.addEvent(eventData);
            $('#eventModal').modal('hide'); // Close the modal after adding the event
        } else {
            alert('Please fill in all required fields.');
        }

    });
    

    // Handle event type change in the modal
    $('#eventType').on('change', function() {
        var selectedType = $(this).val();
        $('#dateGroup, #timeGroup, #locationGroup, #classGroup').hide();
        if (selectedType === 'homework' || selectedType === 'project') {
            $('#dateGroup, #classGroup').show();
        } else if (selectedType === 'class' || selectedType === 'meeting') {
            $('#timeGroup, #locationGroup').show();
        }
    }).trigger('change');
    
});


// Function to convert Canvas API events to FullCalendar events
function convertCanvasEventsToFullCalendarEvents(canvasEvents) {
    return canvasEvents.map(event => {
        return {
            title: event['title'],
            start: event['start_at']
        };
    }).filter(event => event.start); // Filter out events without a start date
}
