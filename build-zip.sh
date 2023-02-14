#!/usr/bin/env bash

plugin="decky-recorder"
docker_name="backend-${plugin,,}"

dockerfile_exists="false"
entrypoint_exists="false"
docker_name="backend-${plugin,,}"
# [ -d $PWD/backend ] && echo "$(ls -lla $PWD/backend | grep Dockerfile)"
[ -f $PWD/backend/Dockerfile ] && dockerfile_exists=true
[ -f $PWD/backend/entrypoint.sh ] && entrypoint_exists=true

#build backend
if [[ "$dockerfile_exists" == "true" ]]; then
  echo "Grabbing provided dockerfile."
  echo "Building provided Dockerfile."
  docker build -f $PWD/backend/Dockerfile -t "$docker_name" .
  mkdir -p /tmp/output/$plugin/backend/out
  # check entrypoint script exists
  if [[ "$entrypoint_exists" == "true" ]]; then
    echo "Running docker image "$docker_name" with provided entrypoint script."
    docker run --rm -i -v $PWD/backend:/backend -v /tmp/output/$plugin/backend/out:/backend/out --entrypoint /backend/entrypoint.sh "$docker_name"
    mkdir -p /tmp/output/$plugin/bin
    cp -rv /tmp/output/$plugin/backend/out/. /tmp/output/$plugin/bin
  else
    echo "Running docker image "$docker_name" with entrypoint script specified in Dockerfile."
    docker run --rm -i -v $PWD/backend:/backend -v /tmp/output/$plugin/backend/out:/backend/out "$docker_name"
    mkdir -p /tmp/output/$plugin/bin
    cp -rv /tmp/output/$plugin/backend/out/. /tmp/output/$plugin/bin
  fi
  docker image rm "$docker_name"
  echo "Built $plugin backend"
# Dockerfile doesn't exist but entrypoint script does, run w/ default image
elif [[ "$dockerfile_exists" == "false" && "$entrypoint_exists" == "true" ]]; then
  echo "Grabbing default docker image and using provided entrypoint script."
  docker run --rm -i -v $PWD/backend:/backend -v /tmp/output/$plugin/backend/out:/backend/out ghcr.io/steamdeckhomebrew/holo-base:latest
  mkdir -p /tmp/output/$plugin/bin
  cp /tmp/output/$plugin/backend/out/. /tmp/output/$plugin/bin
  echo "Built $plugin backend"
else
  echo "Plugin $plugin does not have a backend"
fi

#build frontend
docker run --rm -i -v $PWD:/plugin -v /tmp/output/$plugin:/out ghcr.io/steamdeckhomebrew/builder:latest
echo Built $plugin frontend
ls -lla /tmp/output/$plugin

#make zip
mkdir -p /tmp/zips/
mkdir -p /tmp/output/
cd /tmp/output/${plugin}
zipname=/tmp/zips/${plugin}.zip
echo $plugin
# Names of the optional files (the license can either be called license or license.md, not both)
# (head is there to take the first file, because we're assuming there's only a single license file)
license="$(find . -maxdepth 1 -type f \( -iname "license" -o -iname "license.md" \) -printf '%P\n' | head -n 1)"
readme="$(find . -maxdepth 1 -type f -iname 'readme.md' -printf '%P\n')"
haspython="$(find . -maxdepth 1 -type f -name '*.py' -printf '%P\n')"
# Check if plugin has a bin folder, if so, add "bin" and it's contents to root dir
hasbin="$(find . -maxdepth 1 -type d -name 'bin' -printf '%P\n')"
# Check if plugin has a defaults folder, if so, add "default" contents to root dir
hasdefaults="$(find . -maxdepth 1 -type d -name 'defaults' -printf '%P\n')"
#          if [[ "${{ secrets.STORE_ENV }}" == "testing" ]]; then
#            long_sha="${{ github.event.pull_request.head.sha || github.sha }}"
#            sha=$(echo $long_sha | cut -c1-7)
#            cat $plugin/package.json | jq --arg jqsha "$sha" '.version |= . + "-" + $jqsha' | sudo tee $plugin/$sha-package.json
#            sudo mv $plugin/$sha-package.json $plugin/package.json
#          fi
# Add required plugin files (and directory) to zip file
echo "dist plugin.json package.json"
zip -r $zipname "dist" "plugin.json" "package.json"
if [ ! -z "$hasbin" ]; then
  ls -al bin
  echo "/bin"
  zip -r $zipname "bin"
fi
if [ ! -z "$haspython" ]; then
  echo "*.py"
  find . -maxdepth 1 -type f -name '*.py' -exec zip -r $zipname {} \;
fi
if [ ! -z "$hasdefaults" ]; then
  export workingdir=$PWD
  cd defaults
  export plugin="$plugin"
  export zipname="$zipname"
  if [ ! -f "defaults.txt" ]; then
    find . -mindepth 1 -type d,f -name '*' -exec bash -c '
                for object do
                  outdir="/tmp/output"
                  name="$(basename $object)"
                  # echo "object = $object, name = $name"
                  if [ -e "$object" ]; then
                    sudo mv "$object" $outdir/$plugin/$name
                    moved="$?"
                    # echo "moved = $moved"
                    cd $workingdir
                    if [ "$moved" = "0" ]; then
                      zip -r $zipname $plugin/$name
                    fi
                  fi
                done
              ' find-sh {} +
  else
    if [[ ! "$plugin" =~ "plugin-template" ]]; then
      printf "${red}defaults.txt found in defaults folder, please remove either defaults.txt or the defaults folder.${end}\n"
    else
      printf "plugin template, allowing defaults.txt\n"
    fi
  fi
  cd "$workingdir"
fi
# Check if other files exist, and if they do, add them
echo "license:$plugin/$license readme:$plugin/$readme"
if [ ! -z "$license" ]; then
  zip -r $zipname "$license"
fi
if [ ! -z "$readme" ]; then
  zip -r $zipname "$readme"
fi