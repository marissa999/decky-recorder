# This is the default target, which will be built when 
# you invoke make
current_dir = $(shell pwd)
.PHONY: all
all:
	docker build -t decky-recorder-backend .
	docker run --rm -i -v $(current_dir):/backend -v $(current_dir)/out:/backend/out --entrypoint /backend/entrypoint.sh decky-recorder-backend