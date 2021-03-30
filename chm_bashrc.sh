config_file=$(python3 -c "import sys; sys.path.append(\"${src_dir}\"); import chassis_manager; print(chassis_manager._get_config_file_path())")

is_init()
{
  if [ ! -f "$config_file" ]; then
    echo "Chassis is not initialized. Please execute command 'c_init' to initialize"
    return 1
  fi

  return 0
}

c_lock()
{
  is_init || return
  read -p "Please tell me your pavilion email address: " email
  read -p "What kind of lock would you like to acquire(Exclusive/Shared) [Exclusive]: " lock_type
  lock_type=${lock_type:-'Exclusive'}
  read -p "If the lock is not available, would like to be notified when the lock is available(y/n) [y]: " notify
  notify=${notify:-'y'}

  if [[ "${notify}" == "y" ]]
  then
    python3 ${src_dir}/main.py --lock --lock-type "${lock_type}" --name "shell" --email "${email}" --notify
  else
    python3 ${src_dir}/main.py --lock --lock-type "${lock_type}" --name "shell" --email "${email}"
  fi
}

c_unlock()
{
  is_init || return
  read -p "Please tell me your pavilion email address: " email
  python3 ${src_dir}/main.py --unlock --email "${email}"

}

c_init()
{
  read -p "Please specify a name this chassis: " name
  read -p "Please specify the IP of this chassis: " ip
  python3 ${src_dir}/main.py --init --chname "${name}" --chip "${ip}"

}


c_history()
{
  is_init || return
  python3 ${src_dir}/main.py --lock-history
}

c_owners()
{
  is_init || return
  python3 ${src_dir}/main.py --lock-owners
}

c_gitdir()
{
  is_init || return
  read -p "Please tell me the directory path: " path
  python3 ${src_dir}/main.py --git-init "${path}"
}
