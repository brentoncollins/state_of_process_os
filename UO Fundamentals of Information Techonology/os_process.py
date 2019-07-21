import pandas as pd

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)


class Process:
	def __init__(self, objects, cpu_max_run_time, fifo_lifo):
		self.cpu_max_runtime = cpu_max_run_time
		self.new = objects
		self.input = []
		self.ready = []
		self.running = []
		self.blocked = []
		self.output = []
		self.terminated = []
		self.us = 10

		self.df = pd.DataFrame(
			columns=[
				'μs', 'NEW DATA', 'INPUT', 'READY', 'RUNNING',
				'BLOCKED', 'OUTPUT', 'TERMINATED'])
		if fifo_lifo is True:
			self.fifo_lifo = 0
		else:
			self.fifo_lifo = -1

		self.total_objects = len(self.new)

	def run_process(self):

		self.df = self.ad_df_row(
			self.df, self.us, self.new, self.input,
			self.ready,
			self.running, self.blocked, self.output,
			self.terminated)

		while len(self.terminated) < self.total_objects:
			if self.fifo_lifo == 0:
				self.check_running()
				self.check_ready()
				self.check_input()
				self.check_output()
				self.check_blocked()
				self.check_new()
				self.time_elapsed()


			else:
				self.check_running()
				self.check_input()
				self.check_ready()
				self.check_output()
				self.check_blocked()
				self.check_new()
				self.time_elapsed()


		print(self.df.to_string(index=False))

	def check_output(self):
		"""Checks values in the output state and moves them to
		terminated if they have spend enough time in the output state"""

		# start at the output, if there is something in there and the
		# output timer is up move it to terminated then remove from output
		# if there is something in there with time left remove 10us
		if len(self.output) > 0:
			if self.output[self.fifo_lifo].output == 0:
				self.terminated.append(self.output[self.fifo_lifo])
				self.output.pop(self.fifo_lifo)

	def check_running(self):
		"""Checks data in the running state, moved items into ready if
		have exceeded the max cpu run time, output if the run time has
		finished or blocked if output is occupied."""

		# move to running, if there is something in running and
		# its equal to 0 then move to output. if output has something in
		# it move it to blocked.
		if len(self.running) > 0:
			self.running[0].cpu_run_time += 10

			if self.running[0].cpu_running == 0:
				if len(self.output) == 0:
					self.output.append(self.running[self.fifo_lifo])
					self.running.pop(self.fifo_lifo)
				else:
					self.blocked.append(self.running[self.fifo_lifo])
					self.running.pop(self.fifo_lifo)
			elif self.running[0].cpu_run_time == self.cpu_max_runtime:
				self.running[self.fifo_lifo].cpu_run_time = 0
				if self.fifo_lifo == 0:
					self.ready.append(self.running[self.fifo_lifo]) # this adds
				# to end of list to get whatever out of running then it is
				# the next thing to go back in?
				else:
					self.ready.insert(0, self.running[0])
				self.running.pop(self.fifo_lifo)

	def check_ready(self):
		"""Checks the ready state and moves into running if not occupied"""

		if len(self.ready) > 0 and len(self.running) == 0:
			self.running.append(self.ready[self.fifo_lifo])
			self.ready.pop(self.fifo_lifo)

	def check_input(self):
		"""Checks the running state if there is nothing in ready or running
		move data straight into running."""
		if len(self.input) > 0:
			# If the data has spent enough time in the input area move
			# to running
			if self.input[self.fifo_lifo].input == 0 and len(
					self.running) == 0:
				self.running.append(self.input[self.fifo_lifo])
				self.input.pop(self.fifo_lifo)
			elif self.input[self.fifo_lifo].input == 0 and len(
					self.running) != 0:
				self.ready.append(self.input[self.fifo_lifo])
				self.input.pop(self.fifo_lifo)

	def check_blocked(self):
		"""Check the blocked state, if it still requires input cpu time wait
		until the input is empty, if input time has run check the output
		time and append to output when it is not occupied."""
		if self.fifo_lifo == 0:
			# FIFO
			if len(self.blocked) > 0:
				for index, x in enumerate(self.blocked):
					if x.input != 0 and len(self.input) != 0:
						pass
					if x.input != 0 and len(self.input) == 0:
						self.input.append(self.blocked[self.fifo_lifo])
						self.blocked.pop(index)
					if x.input == 0 and len(self.output) == 0:
						self.output.append(self.blocked[self.fifo_lifo])
						self.blocked.pop(index)
		else:
			# LIFO
			if len(self.blocked) > 0:
				for index, x in enumerate(self.blocked[::-1]):
					if x.input != 0 and len(self.input) != 0:
						pass
					if x.input != 0 and len(self.input) == 0:
						self.input.append(self.blocked[self.fifo_lifo])
						self.blocked.pop(len(self.blocked) - 1)
					if x.input == 0 and len(self.output) == 0:
						self.output.append(self.blocked[self.fifo_lifo])
						self.blocked.pop(len(self.blocked) - 1)

	def check_new(self):
		"""Check if any items in input,if not move to input, if occupied
		move to blocked"""

		# Check if the waiting data is available
		if len(self.new) > 0:
			# If there is nothing waiting in the input move the first item
			# in the list to the input bay.
			if len(self.input) == 0:
				self.input.append(self.new[self.fifo_lifo])
				# Remove the data from the new object list.
				self.new.pop(self.fifo_lifo)
			else:
				# If there is something in the input move to blocked
				self.blocked.append(self.new[self.fifo_lifo])
				# Remove the data from the new object list.
				self.new.pop(self.fifo_lifo)

	def time_elapsed(self):
		"""Subtract the time from each state"""
		self.us += 10
		# Add the row to the data frame
		self.df = self.ad_df_row(self.df, self.us, self.new, self.input,
		                         self.ready,
		                         self.running, self.blocked, self.output,
		                         self.terminated)

		if len(self.input) > 0:
			self.input[0].input -= 10

		if len(self.running) > 0:
			self.running[0].cpu_running -= 10

		if len(self.output) > 0:
			self.output[0].output -= 10
		# Move forward in time by 10 us



		# Set the new dataframe row.


	def ad_df_row(self, df, us, new, data_input, ready, running, blocked,
	              output, terminated):
		"""Add new row to dataframe"""

		df2 = {
			'μs': us, 'NEW DATA': [x.process for x in new],
			'INPUT': [{x.process:x.input} for x in data_input],
			'READY': [x.process for x in ready],
			'RUNNING': [{x.process:x.cpu_running} for x in running],
			'BLOCKED': [x.process for x in blocked],
			'OUTPUT': [{x.process:x.output} for x in output],
			'TERMINATED': [x.process for x in terminated]}

		df = df.append(df2, ignore_index=True)

		return df


class NewProcess:
	def __init__(self, data, input_runtime, cpu_runtime, output_runtime):
		self.process = data
		self.input = input_runtime
		self.cpu_running = cpu_runtime
		self.output = output_runtime
		self.cpu_run_time = 0


# INSTRUCTIONS #
# You will need to install an external library called pandas for this to work.
# It was the best way to visualise the output table.

# Create as many data processes
process_a = NewProcess(
				data='A', input_runtime=10, cpu_runtime=50, output_runtime=30
						)
process_b = NewProcess(
				data='B', input_runtime=10, cpu_runtime=30, output_runtime=40
						)
process_c = NewProcess(
				data='C', input_runtime=30, cpu_runtime=20, output_runtime=10
						)
process_d = NewProcess(
				data='D', input_runtime=20, cpu_runtime=10, output_runtime=10
						)

# Put data processes into a list
process_list = [process_a, process_b, process_c, process_d]

# Create a new object by passing the list of data objects, the max CPU run
# time and setting fifo_lifo to True for FIFO and False for LIFO
run = Process(process_list, cpu_max_run_time=20, fifo_lifo=True)
run.run_process()
