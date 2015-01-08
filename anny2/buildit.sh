#!/bin/bash

#why am I scripting to my script?  nonetheless in bash...
if [[ -z $1 ]]
then
    echo "You need to supply the sample directory as the first argument"
    exit
fi

debug=true
package=org.test.catchphrasepackage
name="catchrase name"
#dir=~/projects/netcheck/
dir=/home/brian/PycharmProjects/kivy_catch_phrase/anny
version=0.1
orientation='portrait'
jars=()
perms=('INTERNET' 'VIBRATE' 'WAKE_LOCK' 'WRITE_EXTERNAL_STORAGE')



jar_options=()
for j in "${jars[@]}"
do
    jar_options+=(--add-jar "$j")
done

perm_options=()
for p in "${perms[@]}"
do
    perm_options+=(--permission "$p")
done

if $debug
then
    mode=('debug' 'installd')
else
    mode=('release')
fi

command=(./build.py --package "$package" --version $version --orientation "$orientation" --name "$name" --dir "$dir" --wakelock)
command+=("${jar_options[@]}" "${perm_options[@]}" "${mode[@]}")

#echo "${command[@]}"
"${command[@]}"
