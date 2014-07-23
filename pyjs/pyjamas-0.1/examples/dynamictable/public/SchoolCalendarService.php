<?
include_once("phpolait/phpolait.php");

class SchoolCalendarService {
	function getPeople($start_row, $max_rows) {
		global $calendar_generator;
		
		return $calendar_generator->getPeople($start_row, $max_rows);
	}
}

function timeslot_compare($a, $b) {
	if ($a["dayOfWeek"] < $b["dayOfWeek"]) return -1;
	else if ($a["dayOfWeek"] > $b["dayOfWeek"]) return 1;
	else {
		if ($a["startMinutes"] < $b["startMinutes"]) return -1;
		else if ($a["startMinutes"] > $b["startMinutes"]) return 1;
	}

	return 0;
}

class SchoolCalendarGenerator {
	function SchoolCalendarGenerator() {
		$this->people = array();
		mt_srand(3);
		$this->CLASS_LENGTH_MINS = 50;
		$this->MAX_SCHED_ENTRIES = 5;
		$this->MIN_SCHED_ENTRIES = 1;
		$this->MAX_PEOPLE = 100;
		$this->STUDENTS_PER_PROF = 5;
		
		$this->FIRST_NAMES = array("Inman", "Sally", "Omar", "Teddy", "Jimmy", 
			"Cathy", "Barney", "Fred", "Eddie", "Carlos");
		$this->LAST_NAMES = array("Smith", "Jones", "Epps", "Gibbs", "Webber",
			"Blum", "Mendez", "Crutcher", "Needler", "Wilson", "Chase", "Edelstein");
		$this->SUBJECTS = array("Chemistry", "Phrenology", "Geometry", 
			"Underwater Basket Weaving", "Basketball", "Computer Science", "Statistics",
			"Materials Engineering", "English Literature", "Geology");

		$this->NO_PEOPLE = array();
		
		$this->generateRandomPeople();
	}
	
	function getPeople($startIndex, $maxCount) {
		$peopleCount = count($this->people);
		
		$start = $startIndex;
		if ($start >= $peopleCount) {
			return $this->NO_PEOPLE;
		}

		$end = min($startIndex + $maxCount, $peopleCount);
		if ($start == $end) {
			return $this->NO_PEOPLE;
		}

		$resultCount = $end - $start;
		$results = array();
		for ($from = $start, $to = 0; $to < $resultCount; ++$from, ++$to) {
			$results[$to] = $this->people[$from];
		}
		return $results;
	}

	function generateRandomPeople() {
		for ($i = 0; $i < $this->MAX_PEOPLE; ++$i) {
			$this->people[]=$this->generateRandomPerson();
		}
	}
			
	function generateRandomPerson() {
		if (mt_rand(0, $this->STUDENTS_PER_PROF) == 1) {
			return $this->generateRandomProfessor();
		} else {
			return $this->generateRandomStudent();
		}
	}

	function generateRandomProfessor() {
		$prof = array();
		
		$firstName = $this->pickRandomString($this->FIRST_NAMES);
		$lastName = $this->pickRandomString($this->LAST_NAMES);
		
		$prof["__jsonclass__"]=array("Professor.Professor");
		$prof["name"]="Dr. " . $firstName . " " . $lastName;
		
		$subject = $this->pickRandomString($this->SUBJECTS);
		$prof["description"]="Professor of " . $subject;
		
		$prof["teachingSchedule"]=$this->generateRandomSchedule();

		return $prof;
	}

	function generateRandomSchedule() {
		$schedule = array();
		$schedule["__jsonclass__"]=array("Schedule.Schedule");
		
		$range = $this->MAX_SCHED_ENTRIES - $this->MIN_SCHED_ENTRIES + 1;
		$howMany = $this->MIN_SCHED_ENTRIES + mt_rand(0, $range);
		
		$timeSlots = array();

		for ($i = 0; $i < $howMany; ++$i) {
			$startHrs = 8 + mt_rand(0, 9);
			$startMins = 15 * mt_rand(0, 4);
			$dayOfWeek = 1 + mt_rand(0, 5);
			
			$absStartMins = 60 * $startHrs + $startMins;
			$absStopMins = $absStartMins + $this->CLASS_LENGTH_MINS;
			
			$timeSlots[$i] = array(
				"__jsonclass__"=>array("TimeSlot.TimeSlot"),
				"dayOfWeek"=>$dayOfWeek,
				"startMinutes"=>$absStartMins,
				"endMinutes"=>$absStopMins
				);
		}

		usort($timeSlots, "timeslot_compare");
		
		$schedule["timeSlots"] = $timeSlots;

		return $schedule;
	}

	function generateRandomStudent() {
		$student = array();
		$student["__jsonclass__"]=array("Student.Student");
		
		$firstName = $this->pickRandomString($this->FIRST_NAMES);
		$lastName = $this->pickRandomString($this->LAST_NAMES);
		$student["name"]=$firstName . " " . $lastName;
		
		$subject = $this->pickRandomString($this->SUBJECTS);
		$student["description"]="Majoring in " . $subject;
		
		$student["classSchedule"]=$this->generateRandomSchedule();
		
		return $student;
	  }

	function pickRandomString($a) {
		return $a[array_rand($a)];	
	}
}

$calendar_generator = new SchoolCalendarGenerator();
$service = new SchoolCalendarService();

$server = new JSONRpcServer($service);
?>