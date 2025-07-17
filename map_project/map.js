


const mapContainer = document.getElementById('map-container'); // 获取地图容器
const textbox = document.getElementById('region-name'); //text box 容器
// 获取所有的区域（path）
const regions = document.querySelectorAll('#hongkong-map path');

// 鼠标悬浮时高亮当前区域
regions.forEach(region => {
    //鼠标移动事件
    region.addEventListener('mouseover',function(event){
        const mouseX = event.clientX;
        const mouseY = event.clientY;
        textbox.style.left = mouseX+'px';
        textbox.style.top= mouseY+'px';
        const name=region.getAttribute("name");
        textbox.textContent = name;
        textbox.style.display = 'block';
        
    });

    region.addEventListener('mouseout', function() {
        textbox.style.display = 'none';     // 隐藏地区名称
    });

});

//试一下把path的路径和属性存进json然后用JavaScript逐个生成？
//把json文件移到JavaScript里直接读取

