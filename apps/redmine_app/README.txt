sudo ./install_binary_dependencies.sh
dependencies/ruby_vuln/compile.sh
sudo dependencies/ruby_vuln/install.sh
./compile_dependencies.sh
sudo ./install_dependencies.sh
sudo ./install_gems.sh
mysql -u root -p < mysql.batch
sudo ./install_redmine.sh
sudo ./launch_redmine.sh

