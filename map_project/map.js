/** 
const cmap = new mapsvg.map(
   "map-container",
  {
    options: {
      source: "C:\internship\AITO\map_project\project\hong-kong.svg",
      loadingText: "Loading map...",
    },
  }
)
const existingMap = mapsvg.get(0);
**/

let scale = 1;  // 当前缩放比例
const scaleStep = 0.05; // 每次滚动的缩放步长
const minScale = 1;  // 最小缩放比例
const maxScale = 3;    // 最大缩放比例

const map = document.getElementById('map'); // 获取SVG地图
const mapContainer = document.getElementById('map-container'); // 获取地图容器

// 获取所有的区域（path）
const regions = document.querySelectorAll('#hongkong-map path');
const regionNameDisplay = document.getElementById('region-name');

// 鼠标悬浮时高亮当前区域
regions.forEach(region => {
    region.addEventListener('mouseover', function(event) {
        const regionName = this.getAttribute('name');  
        regionNameDisplay.textContent = regionName;  // 更新显示的地区名
        regionNameDisplay.style.display = 'block';    // 显示区域名称

        // 根据鼠标位置调整文本框位置
        const mouseX = event.pageX; // 鼠标X坐标
        const mouseY = event.pageY; // 鼠标Y坐标
        console.clear(); // 清除控制台
        console.log(`X: ${event.clientX}, Y: ${event.clientY}`); 

        regionNameDisplay.style.left = mouseX-350 + 'px';  // 这个可以调整弹出来的文本位置，相对于鼠标位置
        regionNameDisplay.style.top = mouseY-300 + 'px';   

        this.classList.add('highlight');  // 高亮当前区域
                

    });


    // 移除高亮
    region.addEventListener('mouseout', function() {
        regionNameDisplay.style.display = 'none';     // 隐藏地区名称
        this.classList.remove('highlight');           // 移除高亮
    });
});

